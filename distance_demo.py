import rp2
import machine
from machine import Pin


from distance_pio import distance

ECHO_PIN = 16
TRIGGER_PIN = 17

CM_MAX = 50
CM_PRECISION = 0.1
# CM_PRECISION  = CM_PER_LOOP = (2 cycles per loop) * (34300 cm/s) / cycles_per_second / 2 (there and back)
STATE_MACHINE_FREQUENCY = int(2 * 34300.0 / CM_PRECISION / 2.0)
MAX_LOOPS = int(CM_MAX / CM_PRECISION)
print(f"STATE_MACHINE_FREQUENCY: {STATE_MACHINE_FREQUENCY}, MAX_LOOPS: {MAX_LOOPS}")


def demo_distance():
    print("Hello, distance!")
    
    pio1 = rp2.PIO(1)
    pio1.remove_program()
    trigger = Pin(TRIGGER_PIN, Pin.OUT)
    echo = Pin(ECHO_PIN, Pin.IN)
    distance_state_machine = rp2.StateMachine(4, distance, freq=STATE_MACHINE_FREQUENCY, set_base=trigger, in_base=echo, jmp_pin=echo)

    try:
        distance_state_machine.active(1)  # Start the PIO state machine
        distance_state_machine.put(MAX_LOOPS)
        while True:
            end_cycles = distance_state_machine.get()
            distance_cm = end_cycles_to_distance_cm(end_cycles)
            print(f"Distance: {distance_cm} cm, end_cycles: {end_cycles}")
    except KeyboardInterrupt:
        print("distance demo stopped.")
    finally:
        distance_state_machine.active(0)

def end_cycles_to_distance_cm(end_cycles):
    if end_cycles == 0xFFFFFFFF:
        return None
    distance_cm = (MAX_LOOPS - end_cycles) * CM_PRECISION
    return distance_cm

demo_distance()