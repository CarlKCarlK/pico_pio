#![no_std]
#![no_main]

use core::num::NonZeroU16;

use defmt::info;
use defmt_rtt as _;
use embassy_executor::{SpawnError, Spawner};
use embassy_futures::select::{select, Either};
use embassy_rp::gpio;
use embassy_sync::{
    blocking_mutex::raw::CriticalSectionRawMutex, channel::Channel, signal::Signal,
};
use embassy_time::{Duration, Instant, Timer};
use panic_probe as _;
use theremin::{Hardware, Never, Result};

#[embassy_executor::main]
async fn main(spawner: Spawner) -> ! {
    // If it returns, something went wrong.
    let err = inner_main(spawner).await.unwrap_err();
    panic!("{err}");
}

async fn inner_main(spawner: Spawner) -> Result<Never> {
    info!("Hello, theremin no PIO!");
    let hardware: Hardware<'_> = Hardware::default();

    static DISTANCE_NOTIFIER: DistanceNotifier = Distance::notifier();
    let trigger_pin = gpio::Output::new(hardware.trigger, gpio::Level::Low);
    let echo_pin = gpio::Input::new(hardware.echo, gpio::Pull::Down);
    let distance = Distance::new(trigger_pin, echo_pin, &DISTANCE_NOTIFIER, spawner)?;
    info!("Distance created");
    loop {
        let distance = distance.measure().await;
        if let Some(distance) = distance {
            info!("Distance: {} cm", distance);
        } else {
            info!("Distance: Too far");
        }
        // Timer::after(Duration::from_millis(100)).await;
    }

    // static SOUND_NOTIFIER: SoundNotifier = Sound::notifier();
    // let buzzer_pin = gpio::Output::new(hardware.buzzer, gpio::Level::Low);
    // let sound = Sound::new(buzzer_pin, &SOUND_NOTIFIER, spawner)?;
    // info!("Sound created");
    // for (frequency, ms, lyrics) in TWINKLE_TWINKLE.iter() {
    //     if *frequency > 0 {
    //         info!("{} -- Frequency: {}", lyrics, frequency);
    //         sound.play(NonZeroU16::new(*frequency).unwrap()).await;
    //         Timer::after(Duration::from_millis(*ms)).await; // Wait as the tone plays
    //         sound.rest().await;
    //         Timer::after(Duration::from_millis(50)).await; // Give a short pause between notes
    //     } else {
    //         sound.rest().await;
    //         Timer::after(Duration::from_millis(*ms + 50)).await; // Wait for the rest duration + a short pause
    //     }
    // }
    // sound.rest().await;

    // // run forever
    // loop {
    //     Timer::after(Duration::from_secs(3_153_600_000)).await; // 100 years
    // }
}

pub struct Sound<'a>(&'a SoundNotifier);
pub type SoundNotifier = Channel<CriticalSectionRawMutex, Option<NonZeroU16>, 4>;
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

    pub async fn play(&self, frequency: NonZeroU16) {
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
    let mut notification: Option<NonZeroU16> = None;
    loop {
        match notification {
            None => {
                buzzer_pin.set_low();
                notification = notifier.receive().await;
            }
            Some(frequency) => {
                let half_duration = Duration::from_micros(1_000_000 / (frequency.get() as u64 * 2));
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

const TWINKLE_TWINKLE: [(u16, u64, &str); 16] = [
    // Bar 1
    (262, 400, "Twin-"), // C
    (262, 400, "-kle"),  // C
    (392, 400, "twin-"), // G
    (392, 400, "-kle"),  // G
    (440, 400, "lit-"),  // A
    (440, 400, "-tle"),  // A
    (392, 800, "star"),  // G
    (0, 400, ""),        // rest
    // Bar 2
    (349, 400, "How"),  // F
    (349, 400, "I"),    // F
    (330, 400, "won-"), // E
    (330, 400, "-der"), // E
    (294, 400, "what"), // D
    (294, 400, "you"),  // D
    (262, 800, "are"),  // C
    (0, 400, ""),       // rest
];

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

const CM_MAX: f32 = 50.0;
const CM_RESOLUTION: f32 = 0.1;
const CM_PER_SECOND: f32 = 34300.0; // speed of sound in cm/s

async fn inner_device_loop_distance(
    mut trigger_pin: gpio::Output<'static>,
    mut echo_pin: gpio::Input<'static>,
    notifier: &'static DistanceNotifier,
) -> Result<Never> {
    // wait 2ms to settle
    Timer::after(Duration::from_micros(2_000)).await;

    const CM_PER_SECOND: f32 = 34300.0; // speed of sound in cm/s
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
                Some(
                    (duration.as_micros() as f32 * CM_PER_SECOND
                        / 2.0
                        / 1_000_000.0
                        / CM_RESOLUTION) as u32 as f32
                        * CM_RESOLUTION,
                )
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
