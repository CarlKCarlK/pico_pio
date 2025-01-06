import rp2
from machine import Pin
import time

CLOCK_FREQUENCY = 125_000_000  # 125 MHz
BUZZER_PIN = 15 
START_CYCLES = 400_000
ECHO_PIN = 16
TRIGGER_PIN = 17
# (2 cycles per loop) * (34300 cm/s) / cycles_per_second / 2 (there and back)
CM_PER_LOOP = 2 * 34300.0 / CLOCK_FREQUENCY / 2.0

# cmk better names
F_LOW = 123.47  # Precomputed lower frequency (~123.47 Hz)
N_OCTAVES = 2.5 #  Total number of octaves
D_MAX = 100.0   # Maximum distance in cm

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

    # Bar 3
    (392, 400, "Up"),     # G
    (392, 400, "a-"),     # G
    (349, 400, "-bove"),  # F
    (349, 400, "the"),    # F
    (330, 400, "world"),  # E
    (330, 400, "so"),     # E
    (294, 800, "high"),   # D

    # Bar 4 
    (392, 400, "Like"),   # G
    (392, 400, "a"),      # G
    (349, 400, "dia-"),   # F
    (349, 400, "-mond"),  # F
    (330, 400, "in"),     # E
    (330, 400, "the"),    # E
    (294, 800, "sky"),    # D

    # Bar 1 (repeat)
    (262, 400, "Twin-"),  # C
    (262, 400, "-kle"),   # C
    (392, 400, "twin-"),  # G
    (392, 400, "-kle"),   # G
    (440, 400, "lit-"),   # A
    (440, 400, "-tle"),   # A
    (392, 800, "star"),   # G

    # Bar 2 (repeat)
    (349, 400, "How"),    # F
    (349, 400, "I"),      # F
    (330, 400, "won-"),   # E
    (330, 400, "-der"),   # E
    (294, 400, "what"),   # D
    (294, 400, "you"),    # D
    (262, 800, "are"),    # C

    # Long pause
    (0, 1600, "pause")

]

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def sound():
    # Wait for non-zero delay value.
    label("wait_for_nonzero")
    pull(block)                     # Wait for a delay value, keep it in osr.
    mov(x, osr)                     # Copy the delay into x.
    jmp(not_x, "wait_for_nonzero")  # If delay is zero, wait for a non-zero value.

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
    jmp(not_x, "wait_for_nonzero")  # If x is zero, wait for a non-zero value.
    wrap()                          # Continue playing the sound.

def demo_sound():
    pio0 = rp2.PIO(0)
    pio0.remove_program()
    sound_state_machine = rp2.StateMachine(0, sound,set_base=Pin(BUZZER_PIN))

    try:
        sound_state_machine.active(1)
        while True:
            for (frequency, ms, lyric) in twinkle_twinkle:
                print(lyric)
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


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def distance():
    # x is the last value sent. Initialize it to 
    # u32::MAX which means 'echo timeout'
    # (Set x to u32::MAX by subtracting 1 from 0)
    set(x, 0)
    label("unused")
    jmp(x_dec, "unused")

    # Read the max echo wait into osr.
    pull()
    # set(x, 400000)
    # mov(osr, x)
    
    # Take a measurement loop
    wrap_target()

    # Generate 10μs trigger pulse (1250 cycles at 125MHz)
    set(pins, 1)                    # Set trigger pin to high voltage
    set(y, 25)                      # Setup loop counter (25 × 50 cycles = 1250)
    label("trigger_pulse_loop")
    nop() [31]                      # Delay 32 cycles
    jmp(y_dec, "trigger_pulse_loop") [17]  # 18 cycles (50 total per iteration)

    set(pins, 0)                    # Set trigger pin to low voltage
    
    wait(1, pin, 0)                 # Wait for echo pin to be high voltage
    mov(y, osr)                     # Load max echo wait into y

    # Count down the echo wait
    label("measure_echo_loop")
    jmp(pin, "echo_active")          # if echo voltage is high continue count down
    jmp("measurement_complete")      # if echo voltage is low, measurement is complete
    label("echo_active")
    jmp(y_dec, "measure_echo_loop")  # Continue counting down unless timeout
    
    
    # y tells where the echo countdown stopped. It
    # will be u32::MAX if the echo timed out.
    label("measurement_complete")
    jmp(x_not_y, "send_result")     # if measurement is different, then sent it.
    jmp("cooldown_cycle")           # If measurement is the same, don't send.
    # Send the measurement
    label("send_result")
    mov(isr, y)                     # Store result in ISR
    push()                          # Send to FIFO
    mov(x, y)                       # Save the result in x
    
    # Cool down period before next measurement
    # about 30 ms (9 times 400,000 / 125,000,000)
    label("cooldown_cycle")
    mov(y, osr)                     # Load cool down counter
    label("cooldown_loop")
    jmp(y_dec, "cooldown_loop") [8] # Wait before next measurement
    wrap()                          # Restart the measurement loop

def demo_distance():
    print("Hello, distance2!")
    
    pio1 = rp2.PIO(1)
    pio1.remove_program()

    trigger = Pin(TRIGGER_PIN, Pin.OUT)
    echo = Pin(ECHO_PIN, Pin.IN)
    distance_state_machine = rp2.StateMachine(4, distance, set_base=trigger, in_base=echo, jmp_pin=echo)

    print("Distance ...")
    distance_state_machine.active(1)  # Start the PIO state machine
    distance_state_machine.put(START_CYCLES)

    try:
        while True:
                end_cycles = distance_state_machine.get()
                distance_cm = end_cycles_to_distance_cm(end_cycles)
                print(f"Distance: {distance_cm} cm, end_cycles: {end_cycles}")
    except KeyboardInterrupt:
        distance_state_machine.active(0)
        print("Distance stopped.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        distance_state_machine.active(0)  # Ensure state machine is stopped

def end_cycles_to_distance_cm(end_cycles):
    if end_cycles == 0xFFFFFFFF:
        return None
    distance_cm = (START_CYCLES - end_cycles) * CM_PER_LOOP
    return distance_cm

def distance_to_frequency(distance):
    return F_LOW * 2.0** ((distance / D_MAX) * N_OCTAVES)



def make_music():
    print("Hello, music!")
    
    pio0 = rp2.PIO(0)
    pio0.remove_program()
    sound_state_machine = rp2.StateMachine(0, sound, set_base=Pin(BUZZER_PIN))

    pio1 = rp2.PIO(1)
    pio1.remove_program()
    trigger = Pin(TRIGGER_PIN, Pin.OUT)
    echo = Pin(ECHO_PIN, Pin.IN)
    distance_state_machine = rp2.StateMachine(4, distance, set_base=trigger, in_base=echo, jmp_pin=echo)


    print("0Music starting...")
    sound_state_machine.active(1)
    print("1Music starting...")
    distance_state_machine.active(1)
    print("2Music starting...")
    distance_state_machine.put(START_CYCLES)

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

def main():
    print("main4")
    demo_sound()
    # demo_distance()
    # make_music()

main()

