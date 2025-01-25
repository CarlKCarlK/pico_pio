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

const TWINKLE_TWINKLE: [(u32, u64, &str); 16] = [
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

async fn inner_main(_spawner: Spawner) -> Result<Never> {
    info!("Hello, sound!");
    let hardware: Hardware<'_> = Hardware::default();
    let mut pio0 = hardware.pio0;
    let state_machine_frequency = embassy_rp::clocks::clk_sys_freq();
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

    sound_state_machine.set_enable(true);
    for (frequency, ms, lyrics) in TWINKLE_TWINKLE.iter() {
        if *frequency > 0 {
            let half_period = state_machine_frequency / frequency / 2;
            info!("{} -- Frequency: {}", lyrics, frequency);
            // Send the half period to the PIO state machine
            sound_state_machine.tx().push(half_period);
            Timer::after(Duration::from_millis(*ms)).await; // Wait as the tone plays
            sound_state_machine.tx().push(0); // Stop the tone
            Timer::after(Duration::from_millis(50)).await; // Give a short pause between notes
        } else {
            sound_state_machine.tx().push(0); // Play a silent rust
            Timer::after(Duration::from_millis(*ms + 50)).await; // Wait for the rest duration + a short pause
        }
    }
    info!("Disabling sound_state_machine");
    sound_state_machine.set_enable(false);

    // run forever
    loop {
        Timer::after(Duration::from_secs(3_153_600_000)).await; // 100 years
    }
}
