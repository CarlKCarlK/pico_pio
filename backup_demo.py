import rp2


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def back_up():
    pull(block)  # Read the half period of the beep sound.
    mov(isr, osr)  # Store the half period in ISR.
    pull(block)  # Read the period_count.

    wrap_target()  # Start of the main loop.

    # Generate the beep sound.
    mov(x, osr)  # Load period_count into X.
    label("beep_loop")

    set(pins, 1)  # Set the buzzer to high voltage (start the tone).
    mov(y, isr)  # Load the half period into Y.
    label("beep_high_delay")
    jmp(y_dec, "beep_high_delay")  # Delay for the half period.
    set(pins, 0)  # Set the buzzer to low voltage (end the tone).
    mov(y, isr)  # Load the half period into Y.
    label("beep_low_delay")
    jmp(y_dec, "beep_low_delay")  # Delay for the low duration.

    jmp(x_dec, "beep_loop")  # Repeat the beep loop.

    # Silence between beeps.
    mov(x, osr)  # Load the period count into X for outer loop.
    label("silence_loop")

    mov(y, isr)  # Load the half period into Y for inner loop.
    label("silence_delay")
    jmp(y_dec, "silence_delay")[1]  # Delay for two clock cycles (jmp + 1 extra)

    jmp(x_dec, "silence_loop")  # Repeat the silence loop.

    wrap()  # End of the main loop, jumps back to wrap_target for continuous execution.


import machine
from machine import Pin
import time

BUZZER_PIN = 15


def demo_back_up():
    print("Hello, back_up!")
    pio0 = rp2.PIO(0)
    pio0.remove_program()
    state_machine_frequency = machine.freq()
    back_up_state_machine = rp2.StateMachine(0, back_up, set_base=Pin(BUZZER_PIN))

    try:
        back_up_state_machine.active(1)
        half_period = int(state_machine_frequency / 1000 / 2)
        period_count = int(state_machine_frequency * 0.5 / (half_period * 2))
        print(f"half_period: {half_period}, period_count: {period_count}")
        back_up_state_machine.put(half_period)
        back_up_state_machine.put(period_count)
        time.sleep_ms(5_000)
    except KeyboardInterrupt:
        print("back_up demo stopped.")
    finally:
        back_up_state_machine.active(0)


demo_back_up()
