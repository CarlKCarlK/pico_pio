import math

import machine
import rp2
from machine import Pin

from distance_pio import distance
from sound_pio import sound

BUZZER_PIN = 15
ECHO_PIN = 16
TRIGGER_PIN = 17

CM_MAX = 50
CM_PRECISION = 0.1
LOWEST_TONE_FREQUENCY = 123.47  # B2
OCTAVE_COUNT = 2.5  #  to F5


def theremin():
    print("Hello, theremin!")

    pio0 = rp2.PIO(0)
    pio0.remove_program()
    sound_state_machine_frequency = machine.freq()
    sound_state_machine = rp2.StateMachine(0, sound, set_base=Pin(BUZZER_PIN))

    pio1 = rp2.PIO(1)
    pio1.remove_program()
    echo = Pin(ECHO_PIN, Pin.IN)
    distance_state_machine_frequency = int(2 * 34300.0 / CM_PRECISION / 2.0)
    distance_state_machine = rp2.StateMachine(
        4,
        distance,
        freq=distance_state_machine_frequency,
        set_base=Pin(TRIGGER_PIN, Pin.OUT),
        in_base=echo,
        jmp_pin=echo,
    )

    sound_state_machine.active(1)
    distance_state_machine.active(1)
    max_loops = int(CM_MAX / CM_PRECISION)
    distance_state_machine.put(max_loops)

    try:
        while True:
            end_loops = distance_state_machine.get()
            distance_cm = loop_difference_to_distance_cm(max_loops, end_loops)
            if distance_cm is None:
                sound_state_machine.put(0)
            else:
                tone_frequency = distance_to_tone_frequency(distance_cm)
                print(
                    f"Distance: {distance_cm} cm, tone frequency: {tone_frequency} Hz"
                )
                half_period = int(sound_state_machine_frequency / (2 * tone_frequency))
                sound_state_machine.put(half_period)
    except KeyboardInterrupt:
        print("theremin stopped.")
    finally:
        sound_state_machine.active(0)


def loop_difference_to_distance_cm(max_loops, end_loops):
    if end_loops == 0xFFFFFFFF:
        return None
    distance_cm = (max_loops - end_loops) * CM_PRECISION
    return distance_cm


def distance_to_tone_frequency(distance):
    return LOWEST_TONE_FREQUENCY * 2.0 ** ((distance / CM_MAX) * OCTAVE_COUNT)


theremin()
