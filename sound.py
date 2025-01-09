import rp2

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def sound():
    # Wait for non-zero delay value.
    label("resting")
    pull(block)                     # Wait for a delay value, keep it in osr.
    mov(x, osr)                     # Copy the delay into x.
    jmp(not_x, "resting")  # If delay is zero, wait for a non-zero value.

    # Play the sound.
    wrap_target()                   # Start of the play-the-sound loop.

    set(pins, 1)                    # Set the buzzer to high voltage.
    label("high_voltage_loop")
    jmp(x_dec, "high_voltage_loop") # Delay

    set(pins, 0)                    # Set the buzzer to low voltage.
    mov(x, osr)
    label("low_voltage_loop")
    jmp(x_dec, "low_voltage_loop")  # Delay

    # Read a new delay value or keep the current one.
    mov(x, osr)                     # set x, the default value for "pull(nonblock)"
    pull(noblock)                   # Read a new delay value or use the default.
    mov(x, osr)      # cmk
    jmp(not_x, "resting")  # If x is zero, wait for a non-zero value.
    wrap()                          # Continue playing the sound.

import machine
from machine import Pin
import time

CLOCK_FREQUENCY =  machine.freq()
BUZZER_PIN = 15 

twinkle_twinkle = [
    # Bar 1
    (262, 400, "Twin-"),  # C
    (262, 400, "-kle"),   # C
    (392, 400, "twin-"),  # G
    (392, 400, "-kle"),   # G
    (440, 400, "lit-"),   # A
    (440, 400, "-tle"),   # A
    (392, 800, "star"),   # G

    # Bar 2
    (349, 400, "How"),    # F
    (349, 400, "I"),      # F
    (330, 400, "won-"),   # E
    (330, 400, "-der"),   # E
    (294, 400, "what"),   # D
    (294, 400, "you"),    # D
    (262, 800, "are"),    # C

    # long rest
    (0, 1000, ""),       # rest
]
def demo_sound():
    print("Hello, demo sound!2")
    pio0 = rp2.PIO(0)
    pio0.remove_program()
    sound_state_machine = rp2.StateMachine(0, sound,set_base=Pin(BUZZER_PIN))

    try:
        sound_state_machine.active(1)
        while True:
            for (frequency, ms, lyrics) in twinkle_twinkle :
                print(lyrics)
                if frequency > 0:
                    half_period = int(CLOCK_FREQUENCY / frequency / 2)
                    print(f"Frequency: {frequency}, half_period: {half_period}")
                    sound_state_machine.put(half_period)
                    time.sleep_ms(ms)
                    sound_state_machine.put(0)
                    time.sleep_ms(50)
                else:
                    sound_state_machine.put(0)
                    time.sleep_ms(ms + 50)
    except KeyboardInterrupt:
        print("Sound demo stopped.")
    finally:
        sound_state_machine.active(0)

demo_sound()