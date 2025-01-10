import rp2
import machine
from machine import Pin


from distance_pio import distance

CLOCK_FREQUENCY =  machine.freq()
ECHO_PIN = 16
TRIGGER_PIN = 17
START_CYCLES = 400_000
# (2 cycles per loop) * (34300 cm/s) / cycles_per_second / 2 (there and back)
CM_PER_LOOP = 2 * 34300.0 / CLOCK_FREQUENCY / 2.0

def demo_distance():
    print("Hello, distance!")
    
    pio1 = rp2.PIO(1)
    pio1.remove_program()
    trigger = Pin(TRIGGER_PIN, Pin.OUT)
    echo = Pin(ECHO_PIN, Pin.IN)
    distance_state_machine = rp2.StateMachine(4, distance, set_base=trigger, in_base=echo, jmp_pin=echo)

    try:
        distance_state_machine.active(1)  # Start the PIO state machine
        distance_state_machine.put(START_CYCLES)
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
    distance_cm = (START_CYCLES - end_cycles) * CM_PER_LOOP
    return distance_cm

demo_distance()