#![no_std]
#![no_main]

use defmt::info;
use defmt_rtt as _;
use derive_more::derive::{Display, Error, From};
use embassy_executor::Spawner;
use embassy_rp::{
    bind_interrupts,
    config::Config as Rp_Config,
    peripherals::{PIN_15, PIN_16, PIN_17, PIO0, PIO1},
    pio::{Config, Direction, InterruptHandler, Pio},
};
use embassy_time::{Duration, Timer};
use libm::powf;
use panic_probe as _;
use pio_proc::pio_file;

#[embassy_executor::main]
async fn main(spawner: Spawner) -> ! {
    // If it returns, something went wrong.
    let err = inner_main_backup_demo(spawner).await.unwrap_err();
    panic!("{err}");
}

async fn inner_main_backup_demo(_spawner: Spawner) -> Result<Never> {
    info!("Hello, back_up!");
    let hardware: Hardware<'_> = Hardware::default();
    let mut pio0 = hardware.pio0;
    let state_machine_frequency = embassy_rp::clocks::clk_sys_freq();
    let mut back_up_state_machine = pio0.sm0;
    let buzzer_pio = pio0.common.make_pio_pin(hardware.buzzer);
    back_up_state_machine.set_pin_dirs(Direction::Out, &[&buzzer_pio]);
    back_up_state_machine.set_config(&{
        let mut config = Config::default();
        config.set_set_pins(&[&buzzer_pio]); // For set instruction
        let program_with_defines = pio_file!("src/backup.pio");
        let program = pio0.common.load_program(&program_with_defines.program);
        config.use_program(&program, &[]);
        config
    });

    back_up_state_machine.set_enable(true);
    let half_period = state_machine_frequency / 1000 / 2;
    let period_count = state_machine_frequency / (half_period * 2) / 2;
    info!(
        "Half period: {}, Period count: {}",
        half_period, period_count
    );
    back_up_state_machine.tx().push(half_period);
    back_up_state_machine.tx().push(period_count);
    Timer::after(Duration::from_millis(5000)).await; // cmk
    info!("Disabling back_up_state_machine");

    back_up_state_machine.set_enable(false);

    // run forever
    loop {
        Timer::after(Duration::from_secs(60 * 60 * 24)).await;
    }
}

async fn inner_main(_spawner: Spawner) -> Result<Never> {
    let hardware: Hardware<'_> = Hardware::default();
    let mut pio0 = hardware.pio0;

    let mut sound_state_machine = pio0.sm0;
    let buzzer_pio = pio0.common.make_pio_pin(hardware.buzzer);

    sound_state_machine.set_pin_dirs(Direction::Out, &[&buzzer_pio]);
    sound_state_machine.set_config(&{
        let mut config = Config::default();
        config.set_set_pins(&[&buzzer_pio]); // For set instruction
        let program_with_defines = pio_file!("src/sound.pio");
        let program = pio0.common.load_program(&program_with_defines.program);
        config.use_program(&program, &[]);
        config
    });

    let mut pio1 = hardware.pio1;
    let mut distance_state_machine = pio1.sm0;
    let trigger_pio = pio1.common.make_pio_pin(hardware.trigger);
    let echo_pio = pio1.common.make_pio_pin(hardware.echo);

    distance_state_machine.set_pin_dirs(Direction::Out, &[&trigger_pio]);
    distance_state_machine.set_pin_dirs(Direction::In, &[&echo_pio]);
    distance_state_machine.set_config(&{
        let mut config = Config::default();
        config.set_set_pins(&[&trigger_pio]); // For set instruction
        config.set_in_pins(&[&echo_pio]); // For wait instruction
        config.set_jmp_pin(&echo_pio); // For jmp instruction
        let program_with_defines = pio_file!("src/distance.pio");
        let program = pio1.common.load_program(&program_with_defines.program);
        config.use_program(&program, &[]);
        config
    });

    sound_state_machine.set_enable(true);
    distance_state_machine.set_enable(true);
    const START_CYCLES: u32 = 400_000;
    const CLOCK_FREQ: u32 = 125_000_000; // 125 MHz clock frequency
    distance_state_machine.tx().push(START_CYCLES); // cmk const

    loop {
        let end_cycles = distance_state_machine.rx().wait_pull().await;
        let distance_cm = if end_cycles < u32::MAX {
            let diff = START_CYCLES - end_cycles;
            let distance_cm = (diff as f32 * 2.0 / 125e6 * 34300.0) / 2.0;
            info!(
                "Diff: {}, Distance: {:?}, End cycles: {}",
                diff, distance_cm, end_cycles
            );
            Some(distance_cm)
        // cmk const
        } else {
            info!("Distance: None, End cycles: {}", end_cycles);
            None
        };
        if let Some(distance_cm) = distance_cm.filter(|&distance_cm| distance_cm < D_MAX) {
            // map 100 cm to 1000 hz and 0 cm to 1 hz -- linear is OK
            let freq = distance_to_frequency(distance_cm);
            let half_period = CLOCK_FREQ / (2 * freq as u32);
            // sound_sm.restart();
            sound_state_machine.tx().push(half_period);
            // info!("Frequency: {} Hz, Half period: {}", freq as u32, half_period);
        } else {
            // sound_sm.restart();
            sound_state_machine.tx().push(0);
        }
    }
}

const F_LOW: f32 = 123.47; // Precomputed lower frequency (~123.47 Hz)
const N_OCTAVES: f32 = 2.5; // Total number of octaves
const D_MAX: f32 = 100.0; // Maximum distance in cm

#[inline]
fn distance_to_frequency(distance: f32) -> f32 {
    F_LOW * powf(2.0, (distance / D_MAX) * N_OCTAVES)
}

/// Rust's `!` is unstable.  This is a locally-defined equivalent which is stable.
#[derive(Debug)]
pub enum Never {}

// Associate PIO0_IRQ_0 with the interrupt handler for PIO0.
bind_interrupts!(struct Pio0Irqs {
    PIO0_IRQ_0 => InterruptHandler<PIO0>;
});

bind_interrupts!(struct Pio1Irqs {
    PIO1_IRQ_0 => InterruptHandler<PIO1>;
});

/// Minimal Hardware abstraction for the RP2040
pub struct Hardware<'a> {
    pub pio0: Pio<'a, PIO0>,
    pub pio1: Pio<'a, PIO1>,
    pub buzzer: PIN_15,
    pub echo: PIN_16,
    pub trigger: PIN_17,
}

impl Default for Hardware<'_> {
    fn default() -> Self {
        // Initialize Embassy peripherals
        let peripherals = embassy_rp::init(Rp_Config::default());

        // Initialize PIO
        let pio0 = Pio::new(peripherals.PIO0, Pio0Irqs {});
        let pio1 = Pio::new(peripherals.PIO1, Pio1Irqs {});

        // Return the hardware abstraction
        Self {
            pio0,
            pio1,
            buzzer: peripherals.PIN_15,
            echo: peripherals.PIN_16,
            trigger: peripherals.PIN_17,
        }
    }
}

/// A specialized `Result` where the error is this crate's `Error` type.
pub type Result<T, E = Error> = core::result::Result<T, E>;

/// Define a unified error type for this crate.
#[derive(Debug, Display, Error, From)]
pub enum Error {
    #[display("{_0:?}")]
    TaskSpawn(#[error(not(source))] embassy_executor::SpawnError),
}
