#![no_std]

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
