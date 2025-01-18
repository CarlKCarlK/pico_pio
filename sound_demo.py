import rp2
import machine
from machine import Pin
import time

import sound_pio

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
    (0, 400, ""),         # rest

    # Bar 2
    (349, 400, "How"),    # F
    (349, 400, "I"),      # F
    (330, 400, "won-"),   # E
    (330, 400, "-der"),   # E
    (294, 400, "what"),   # D
    (294, 400, "you"),    # D
    (262, 800, "are"),    # C
    (0, 400, ""),         # rest
]

def demo_sound():
    print("Hello, demo sound!")
    pio0 = rp2.PIO(0)
    pio0.remove_program()
    sound_state_machine = rp2.StateMachine(0, sound_pio, set_base=Pin(BUZZER_PIN))

    try:
        sound_state_machine.active(1)
        for (frequency, ms, lyrics) in twinkle_twinkle :
            if frequency > 0:
                half_period = int(CLOCK_FREQUENCY / frequency / 2)
                print(f"'{lyrics}' -- Frequency: {frequency}, half_period: {half_period}")
                sound_state_machine.put(half_period) # Send the half period to the PIO state machine
                time.sleep_ms(ms)                    # Wait as the tone plays
                sound_state_machine.put(0)           # Stop the tone
                time.sleep_ms(50)                    # Give a short pause between notes
            else:
                sound_state_machine.put(0)           # Play a silent rest
                time.sleep_ms(ms + 50)               # Wait for the rest duration + a short pause
    except KeyboardInterrupt:
        print("Sound demo stopped.")
    finally:
        sound_state_machine.active(0)

demo_sound()