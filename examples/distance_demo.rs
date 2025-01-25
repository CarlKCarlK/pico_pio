#![no_std]
#![no_main]

use defmt::info;
use defmt_rtt as _;
use embassy_executor::Spawner;
use embassy_rp::pio::{Config, Direction};
use fixed::FixedU32;
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
const MAX_LOOPS: u32 = CM_MAX * CM_UNITS_PER_CM;

async fn inner_main(_spawner: Spawner) -> Result<Never> {
    info!("Hello, distance!");
    let hardware: Hardware<'_> = Hardware::default();
    let mut pio1 = hardware.pio1;
    let system_frequency = embassy_rp::clocks::clk_sys_freq();
    let state_machine_frequency = 2 * 34_300 * CM_UNITS_PER_CM / 2;
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
        config.clock_divider =
            FixedU32::<U8>::from_num(system_frequency as f32 / state_machine_frequency as f32);
        info!("clock_divider: {}", config.clock_divider.to_num::<f32>());
        config
    });
    info!(
        "state_machine_frequency: {}, max_loops: {}",
        state_machine_frequency, MAX_LOOPS
    );

    let ten_μs = (state_machine_frequency * 10).div_ceil(1_000_000);
    info!("10 microsecond trigger pulse is {} cycles", ten_μs);

    distance_state_machine.set_enable(true);
    distance_state_machine.tx().wait_push(MAX_LOOPS).await;
    loop {
        let end_loops = distance_state_machine.rx().wait_pull().await;
        let distance_cm = loop_difference_to_distance_cm(MAX_LOOPS, end_loops);
        info!("Distance: {} cm, end_loops: {}", distance_cm, end_loops);
    }
}

#[inline]
fn loop_difference_to_distance_cm(max_loops: u32, end_loops: u32) -> Option<f32> {
    if end_loops == u32::MAX {
        return None;
    }
    Some((max_loops - end_loops) as f32 / CM_UNITS_PER_CM as f32)
}
