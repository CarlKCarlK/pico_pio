import math

import machine
import rp2
from machine import Pin

from distance_pio import distance

ECHO_PIN = 16
TRIGGER_PIN = 17

CM_MAX = 50
CM_PRECISION = 0.1


def demo_distance():
    print("Hello, distance2")

    pio1 = rp2.PIO(1)
    pio1.remove_program()
    echo = Pin(ECHO_PIN, Pin.IN)
    # CM_PRECISION  = CM_PER_LOOP = (2 cycles per loop) * (34300 cm/s) / cycles_per_second / 2 (there and back)
    state_machine_frequency = int(2 * 34300.0 / CM_PRECISION / 2.0)
    distance_state_machine = rp2.StateMachine(
        4,  # PIO Block 1, State machine 4
        distance,  # PIO program
        freq=state_machine_frequency,
        in_base=echo,
        set_base=Pin(TRIGGER_PIN, Pin.OUT),
        jmp_pin=echo,
    )
    max_loops = int(CM_MAX / CM_PRECISION)
    print(f"state_machine_frequency: {state_machine_frequency}, max_loops: {max_loops}")

    TEN_μs = math.ceil(10e-6 * state_machine_frequency)
    print(f"10 microsecond trigger pulse is {TEN_μs} cycles")

    try:
        distance_state_machine.active(1)  # Start the PIO state machine
        distance_state_machine.put(max_loops)
        while True:
            end_loops = distance_state_machine.get()
            distance_cm = loop_difference_to_distance_cm(max_loops, end_loops)
            print(f"Distance: {distance_cm} cm, end_loops: {end_loops}")
    except KeyboardInterrupt:
        print("distance demo stopped.")
    finally:
        distance_state_machine.active(0)


def loop_difference_to_distance_cm(max_loops, end_loops):
    if end_loops == 0xFFFFFFFF:
        return None
    distance_cm = (max_loops - end_loops) * CM_PRECISION
    return distance_cm


demo_distance()
