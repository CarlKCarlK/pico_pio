#![no_std]
#![no_main]

use defmt::info;
use defmt_rtt as _;
use embassy_executor::Spawner;
use embassy_rp::pio::{Config, Direction};
use fixed::FixedU32;
use libm::powf;
use panic_probe as _;
use pio_proc::pio_file;
use typenum::U8;

use theremin::{Hardware, Never, Result};

#[embassy_executor::main]
async fn main(spawner: Spawner) -> ! {
    // If it returns, something went wrong.
    let err = inner_main(spawner).await.unwrap_err();
    panic!("{err}");
}

const CM_MAX: u32 = 50;
const CM_UNITS_PER_CM: u32 = 10;
const LOWEST_TONE_FREQUENCY: f32 = 123.47; // B2
const OCTAVE_COUNT: f32 = 2.5; //  to F5

async fn inner_main(_spawner: Spawner) -> Result<Never> {
    info!("Hello, theremin!");
    let hardware: Hardware<'_> = Hardware::default();

    // Set up the sound state machine
    let mut pio0 = hardware.pio0;
    let sound_state_machine_frequency = embassy_rp::clocks::clk_sys_freq();
    let mut sound_state_machine = pio0.sm0;
    let buzzer_pio = pio0.common.make_pio_pin(hardware.buzzer);
    sound_state_machine.set_pin_dirs(Direction::Out, &[&buzzer_pio]);
    sound_state_machine.set_config(&{
        let mut config = Config::default();
        config.set_set_pins(&[&buzzer_pio]); // For set instruction
        let program_with_defines = pio_file!("examples/sound.pio");
        let program = pio0.common.load_program(&program_with_defines.program);
        config.use_program(&program, &[]);
        config
    });

    // Set up the distance state machine
    let mut pio1 = hardware.pio1;
    let system_frequency = embassy_rp::clocks::clk_sys_freq();
    let distance_state_machine_frequency = 2 * 34_300 * CM_UNITS_PER_CM / 2;
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
        let program_with_defines = pio_file!("examples/distance.pio");
        let program = pio1.common.load_program(&program_with_defines.program);
        config.use_program(&program, &[]);
        // Set the clock divider for the desired state machine frequency
        config.clock_divider = FixedU32::<U8>::from_num(
            system_frequency as f32 / distance_state_machine_frequency as f32,
        );
        info!("clock_divider: {}", config.clock_divider.to_num::<f32>());
        config
    });
    let max_loops = CM_MAX * CM_UNITS_PER_CM;

    sound_state_machine.set_enable(true);
    distance_state_machine.set_enable(true);
    distance_state_machine.tx().push(max_loops);
    loop {
        let end_loops = distance_state_machine.rx().wait_pull().await;
        info!("End loops: {}", end_loops);
        match loop_difference_to_distance_cm(max_loops, end_loops) {
            None => {
                info!("Distance: out of range");
                sound_state_machine.tx().push(0);
            }
            Some(distance_cm) => {
                let tone_frequency = distance_to_tone_frequency(distance_cm);
                info!("Distance: {} cm, tone: {} Hz", distance_cm, tone_frequency);
                let half_period = sound_state_machine_frequency / tone_frequency as u32 / 2;
                sound_state_machine.tx().push(half_period);
            }
        }
    }
}

#[inline]
fn loop_difference_to_distance_cm(max_loops: u32, end_loops: u32) -> Option<f32> {
    if end_loops == u32::MAX {
        return None;
    }
    Some((max_loops - end_loops) as f32 / CM_UNITS_PER_CM as f32)
}

#[inline]
fn distance_to_tone_frequency(distance: f32) -> f32 {
    LOWEST_TONE_FREQUENCY * powf(2.0, distance * OCTAVE_COUNT / CM_MAX as f32)
}
