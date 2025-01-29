#![no_std]
#![no_main]

use defmt::info;
use defmt_rtt as _;
use embassy_executor::{SpawnError, Spawner};
use embassy_futures::select::{select, Either};
use embassy_rp::gpio;
use embassy_sync::{
    blocking_mutex::raw::CriticalSectionRawMutex, channel::Channel, signal::Signal,
};
use embassy_time::{Duration, Instant, Timer};
use libm::powf;
use panic_probe as _;
use theremin::{Hardware, Never, Result};

const CM_MAX: f32 = 50.0;
const CM_RESOLUTION: f32 = 0.1;
const CM_PER_SECOND: f32 = 34300.0; // speed of sound in cm/s
const LOWEST_TONE_FREQUENCY: f32 = 123.47; // B2
const OCTAVE_COUNT: f32 = 2.5; //  to F5

#[embassy_executor::main]
async fn main(spawner: Spawner) -> ! {
    // If it returns, something went wrong.
    let err = inner_main(spawner).await.unwrap_err();
    panic!("{err}");
}

async fn inner_main(spawner: Spawner) -> Result<Never> {
    info!("Hello, theremin no PIO!");
    let hardware: Hardware<'_> = Hardware::default();

    let buzzer_pin = gpio::Output::new(hardware.buzzer, gpio::Level::Low);
    let trigger_pin = gpio::Output::new(hardware.trigger, gpio::Level::Low);
    let echo_pin = gpio::Input::new(hardware.echo, gpio::Pull::Down);
    static SOUND_NOTIFIER: SoundNotifier = Sound::notifier();
    let sound = Sound::new(buzzer_pin, &SOUND_NOTIFIER, spawner)?;
    static DISTANCE_NOTIFIER: DistanceNotifier = Distance::notifier();
    let distance = Distance::new(trigger_pin, echo_pin, &DISTANCE_NOTIFIER, spawner)?;

    loop {
        match distance.measure().await {
            None => {
                info!("Distance: out of range");
                sound.rest().await;
            }
            Some(distance_cm) => {
                let tone_frequency = distance_to_tone_frequency(distance_cm);
                info!("Distance: {} cm, tone: {} Hz", distance_cm, tone_frequency);
                sound.play(tone_frequency).await;
                Timer::after(Duration::from_millis(50)).await;
            }
        }
    }
}

pub struct Sound<'a>(&'a SoundNotifier);
pub type SoundNotifier = Channel<CriticalSectionRawMutex, Option<u16>, 4>;
impl Sound<'_> {
    #[must_use]
    pub const fn notifier() -> SoundNotifier {
        Channel::new()
    }

    #[must_use = "Must be used to manage the spawned task"]
    pub fn new(
        buzzer_pin: gpio::Output<'static>,
        notifier: &'static SoundNotifier,
        spawner: Spawner,
    ) -> Result<Self, SpawnError> {
        spawner.spawn(device_loop_sound(buzzer_pin, notifier))?;
        Ok(Self(notifier))
    }

    pub async fn play(&self, frequency: u16) {
        self.0.send(Some(frequency)).await;
    }

    pub async fn rest(&self) {
        self.0.send(None).await;
    }
}

#[embassy_executor::task]
async fn device_loop_sound(
    buzzer_pin: gpio::Output<'static>,
    notifier: &'static SoundNotifier,
) -> ! {
    // should never return
    let err = inner_device_loop_sound(buzzer_pin, notifier).await;
    panic!("{:?}", err);
}

async fn inner_device_loop_sound(
    mut buzzer_pin: gpio::Output<'static>,
    notifier: &'static SoundNotifier,
) -> Result<Never> {
    let mut notification: Option<u16> = None;
    loop {
        match notification {
            None => {
                buzzer_pin.set_low();
                notification = notifier.receive().await;
            }
            Some(frequency) => {
                let half_duration = Duration::from_micros(1_000_000 / (frequency as u64 * 2));
                loop {
                    buzzer_pin.set_high();
                    if let Either::Second(inner_notification) =
                        select(Timer::after(half_duration), notifier.receive()).await
                    {
                        notification = inner_notification;
                        break;
                    }
                    buzzer_pin.set_low();
                    if let Either::Second(inner_notification) =
                        select(Timer::after(half_duration), notifier.receive()).await
                    {
                        notification = inner_notification;
                        break;
                    }
                }
            }
        }
    }
}

pub struct Distance<'a>(&'a DistanceNotifier);
pub type DistanceNotifier = Signal<CriticalSectionRawMutex, Option<f32>>;
impl Distance<'_> {
    #[must_use]
    pub const fn notifier() -> DistanceNotifier {
        Signal::new()
    }

    #[must_use = "Must be used to manage the spawned task"]
    pub fn new(
        trigger_pin: gpio::Output<'static>,
        echo_pin: gpio::Input<'static>,
        notifier: &'static DistanceNotifier,
        spawner: Spawner,
    ) -> Result<Self, SpawnError> {
        spawner.spawn(device_loop_distance(trigger_pin, echo_pin, notifier))?;
        Ok(Self(notifier))
    }

    pub async fn measure(&self) -> Option<f32> {
        self.0.wait().await
    }
}

#[embassy_executor::task]
async fn device_loop_distance(
    trigger_pin: gpio::Output<'static>,
    echo_pin: gpio::Input<'static>,
    notifier: &'static DistanceNotifier,
) -> ! {
    // should never return
    let err = inner_device_loop_distance(trigger_pin, echo_pin, notifier).await;
    panic!("{:?}", err);
}

async fn inner_device_loop_distance(
    mut trigger_pin: gpio::Output<'static>,
    mut echo_pin: gpio::Input<'static>,
    notifier: &'static DistanceNotifier,
) -> Result<Never> {
    // wait 2ms to settle
    Timer::after(Duration::from_micros(2_000)).await;

    let max_duration = Duration::from_micros((1_000_000.0 * CM_MAX * 2.0 / CM_PER_SECOND) as u64);
    let mut previous_measure: Option<f32> = None;
    loop {
        trigger_pin.set_high();
        Timer::after(Duration::from_micros(10)).await;
        trigger_pin.set_low();
        echo_pin.wait_for_high().await;
        let start = Instant::now();
        let measure = match select(Timer::after(max_duration), echo_pin.wait_for_low()).await {
            Either::First(_) => None,
            Either::Second(_) => {
                let duration = Instant::now() - start;
                Some(round(
                    duration.as_micros() as f32 * CM_PER_SECOND / 2.0 / 1_000_000.0,
                ))
            }
        };
        // round measure to CM_RESOLUTION
        if previous_measure != measure {
            notifier.signal(measure);
            previous_measure = measure;
        }
        Timer::after(Duration::from_millis(60)).await;
    }
}

#[inline]
fn distance_to_tone_frequency(distance: f32) -> u16 {
    (LOWEST_TONE_FREQUENCY * powf(2.0, distance * OCTAVE_COUNT / CM_MAX)) as u16
}

#[inline]
fn round(distance: f32) -> f32 {
    (distance / CM_RESOLUTION) as u32 as f32 * CM_RESOLUTION
}
