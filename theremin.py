import rp2
import machine
from machine import Pin
import math

# cmk rename sound sound_pio
from sound_pio import sound
from distance_pio import distance

# cmk better names
BUZZER_PIN = 15 
ECHO_PIN = 16
TRIGGER_PIN = 17
F_LOW = 123.47  # Precomputed lower frequency (~123.47 Hz)
N_OCTAVES = 2.5 #  Total number of octaves
D_MAX = 100.0   # Maximum distance in cm

CM_MAX = 50
CM_PRECISION = 0.1
# CM_PRECISION  = CM_PER_LOOP = (2 cycles per loop) * (34300 cm/s) / cycles_per_second / 2 (there and back)
STATE_MACHINE_FREQUENCY = int(2 * 34300.0 / CM_PRECISION / 2.0)
MAX_LOOPS = int(CM_MAX / CM_PRECISION)
print(f"STATE_MACHINE_FREQUENCY: {STATE_MACHINE_FREQUENCY}, MAX_LOOPS: {MAX_LOOPS}")
# 10 μs trigger pulse is # cycles at STATE_MACHINE_FREQUENCY
TEN_μs = math.ceil(10e-6 * STATE_MACHINE_FREQUENCY)
print(f"TEN_microseconds: {TEN_μs} cycles")

CLOCK_FREQUENCY =  machine.freq()

def distance_to_frequency(distance):
    return F_LOW * 2.0** ((distance / D_MAX) * N_OCTAVES)

def theremin():
    print("Hello, theremin!")
    
    pio0 = rp2.PIO(0)
    pio0.remove_program()
    sound_state_machine = rp2.StateMachine(0, sound, set_base=Pin(BUZZER_PIN))

    pio1 = rp2.PIO(1)
    pio1.remove_program()
    trigger = Pin(TRIGGER_PIN, Pin.OUT)
    echo = Pin(ECHO_PIN, Pin.IN)
    distance_state_machine = rp2.StateMachine(4, distance, freq=STATE_MACHINE_FREQUENCY,set_base=trigger, in_base=echo, jmp_pin=echo)


    print("cmkMusic starting...")
    sound_state_machine.active(1)
    print("cmk1Music starting...")
    distance_state_machine.active(1)
    print("cmkMusic starting...")
    distance_state_machine.put(MAX_LOOPS)

    try:
        while True:
            # print("getting distance")
            end_cycles = distance_state_machine.get()
            print("end_cycles: ", end_cycles)
            distance_cm = end_cycles_to_distance_cm(end_cycles)
            if distance_cm is None:
                sound_state_machine.put(0)
            else:
                freq = distance_to_frequency(distance_cm)
                half_period = int(CLOCK_FREQUENCY / (2 * freq))
                sound_state_machine.put(half_period)
    except KeyboardInterrupt:
        sound_state_machine.active(0)
        print("music stopped.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        sound_state_machine.active(0)  # Ensure state machine is stopped

def end_cycles_to_distance_cm(end_cycles):

    if end_cycles == 0xFFFFFFFF:
        return None
    distance_cm = (MAX_LOOPS - end_cycles) * CM_PRECISION
    return distance_cm

theremin()