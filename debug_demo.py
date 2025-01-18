import rp2
from machine import Pin

from distance_debug_pio import distance


def demo_debug():
    print("Hello, debug!")
    pio1 = rp2.PIO(1)
    pio1.remove_program()
    echo = Pin(16, Pin.IN)
    distance_state_machine = rp2.StateMachine(
        4, distance, freq=343_000, in_base=echo, set_base=Pin(17, Pin.OUT), jmp_pin=echo
    )
    try:
        distance_state_machine.active(1)  # Start the PIO state machine
        distance_state_machine.put(500)
        while True:
            end_loops = distance_state_machine.get()
            print(end_loops)
    except KeyboardInterrupt:
        print("distance demo stopped.")
    finally:
        distance_state_machine.active(0)


demo_debug()
