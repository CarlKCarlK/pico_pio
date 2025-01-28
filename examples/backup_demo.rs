#![no_std]
#![no_main]

use defmt::info;
use defmt_rtt as _;
use embassy_executor::Spawner;
use embassy_rp::pio::{Config, Direction};
use embassy_time::{Duration, Timer};
use panic_probe as _;
use pio_proc::pio_file;

use theremin::{Hardware, Never, Result};

#[embassy_executor::main]
async fn main(spawner: Spawner) -> ! {
    // If it returns, something went wrong.
    let err = inner_main(spawner).await.unwrap_err();
    panic!("{err}");
}

async fn inner_main(_spawner: Spawner) -> Result<Never> {
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
        let program_with_defines = pio_file!("examples/backup.pio");
        let program = pio0.common.load_program(&program_with_defines.program);
        config.use_program(&program, &[]); // No side-set pins
        config
    });

    back_up_state_machine.set_enable(true);
    let half_period = state_machine_frequency / 1000 / 2;
    let period_count = state_machine_frequency / (half_period * 2) / 2;
    info!(
        "Half period: {}, Period count: {}",
        half_period, period_count
    );
    back_up_state_machine.tx().wait_push(half_period).await;
    back_up_state_machine.tx().wait_push(period_count).await;
    Timer::after(Duration::from_millis(5000)).await;
    info!("Disabling back_up_state_machine");

    back_up_state_machine.set_enable(false);

    // run forever
    loop {
        Timer::after(Duration::from_secs(3_153_600_000)).await; // 100 years
    }
}
