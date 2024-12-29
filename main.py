from lcd1602 import LCD
from machine import Pin
import machine # type: ignore
import utime # type: ignore
import _thread
import math
import rp2

shared_distance = [200]  # Shared distance value between cores

# def tone(pin, frequency, duration):
#     print(f"tone {frequency} {duration}")
#     if frequency > 0:
#         pin.freq(frequency)
#         pin.duty_u16(30000)
#         utime.sleep_ms(duration)s
#         pin.duty_u16(0)  # Ensure PWM stops
#     else:
#         utime.sleep_ms(duration)  # Silence duration

lcd=LCD()
buzzer = machine.PWM(machine.Pin(15))


# Note frequencies in Hz
NOTE_FREQUENCIES = {
    'B3': 247,
    'C4': 262,
    'D4': 294,
    'E4': 330,
    'F4': 349,
    'G4': 392,
    'A4': 440,
    'B4': 494,
    'C5': 523,
    'D5': 587,
    'E5': 659,
    'F5': 698,
    'G5': 784,
    'A5': 880,
    'B5': 988,
    'P': 0  # Pause
}

# 'Jingle Bells' melody: (note, duration in beats)
jingle_bells_melody = [
    ('E5', 1), ('E5', 1), ('E5', 2),        # E E E
    ('E5', 1), ('E5', 1), ('E5', 2),        # E E E
    ('E5', 1), ('G5', 1), ('C5', 1), ('D5', 1), ('E5', 4),  # E G C D E
    ('F5', 1), ('F5', 1), ('F5', 1), ('F5', 1),  # F F F F
    ('F5', 1), ('E5', 1), ('E5', 1), ('E5', 1),  # F E E E
    ('E5', 1), ('D5', 1), ('D5', 1), ('E5', 1),  # E D D E
    ('D5', 2), ('G5', 2)  # D G
]

short_melody = [
    ('E5', 1), ('G5', 1), ('C5', 1), ('D5', 1), ('E5', 4),  # E G C D E
 ]

one_melody = [
    ('B3', 1)
 ]

beat_duration_ms = 500  # Duration of a beat in ms

def tone(pin, frequency, duration_ms):
    print(f"tone {frequency} {duration_ms}")
    if frequency == 0:  # Pause
        utime.sleep_ms(int(duration_ms))
    else:
        pin.freq(frequency)
        pin.duty_u16(30_000)
        utime.sleep_ms(int(duration_ms))
        pin.duty_u16(0)


def song(melody):
    # Initialize PWM on GPIO pin 15
    # Play the melody
    for note, duration_beats in melody:
        frequency = NOTE_FREQUENCIES[note]
        tone(buzzer, frequency, duration_beats)
        utime.sleep_ms(int(beat_duration_ms * 0.1))  # Short pause between notes


# Map distance to frequency
def map_distance_to_frequency(distance_cm):
    if distance_cm > 100.0:
        return 0  # Silence for distances > 100
    else:
        # Map 3-60 cm to 200-1000 Hz range
        return int(200.0 + ((distance_cm - 3.0) * (800.0 / (60.0 - 3.0))))

# Measure distance (runs on Core 1)

TRIG = machine.Pin(17, machine.Pin.OUT)
ECHO = machine.Pin(16, machine.Pin.IN)


def measure_distance():
    TRIG.low()
    utime.sleep_us(2)
    TRIG.high()
    utime.sleep_us(10)
    TRIG.low()

    # Timeout for the echo start
    start_time = utime.ticks_us()
    while not ECHO.value():
        if utime.ticks_diff(utime.ticks_us(), start_time) > 100_000:  # 100 ms timeout
            return 200

    time1 = utime.ticks_us()
    while ECHO.value():
        if utime.ticks_diff(utime.ticks_us(), time1) > 100_000:  # 100 ms timeout
            return 200

    time2 = utime.ticks_us()
    duration = utime.ticks_diff(time2, time1)
    distance_cm = float(duration) * 340.0 / 2.0 / 10000.0
    return distance_cm

def snap_to_western_scale(freq):
    if freq <= 0:
        return 0  # Invalid frequency
    
    # Calculate semitones from A4 (440 Hz)
    n = 12 * math.log2(freq / 440.0)
    n_rounded = round(n)  # Round to the nearest semitone

    # Calculate the closest Western note frequency
    closest_freq = 440.0 * (2 ** (n_rounded / 12))

    return int(closest_freq)

# Semitone offsets for black keys relative to an octave
BLACK_KEY_SEMITONES = [1, 3, 6, 8, 10]

def snap_to_black_keys(freq):
    if freq <= 0:
        return 0  # Invalid frequency
    
    # Calculate semitones from A4 (440 Hz)
    n = 12 * math.log2(freq / 440.0)
    base_octave = int(n // 12) * 12  # Find the base octave for n
    fractional_semitone = n % 12

    # Find the closest black key semitone in the current octave
    closest_semitone = min(BLACK_KEY_SEMITONES, key=lambda x: abs(x - fractional_semitone))
    snapped_semitone = base_octave + closest_semitone

    # Convert back to frequency
    snapped_freq = 440.0 * (2 ** (snapped_semitone / 12))
    return round(snapped_freq/2)

amazing_grace_frequencies = [
    77.78,         # D#2 ("A-")
    92.50,         # F#2 ("ma-")
    92.50,         # F#2 ("zing")
    103.83,        # G#2 ("Grace,")
    92.50,         # F#2 ("how")
    77.78,         # D#2 ("sweet")
    69.30, 69.30,  # C#2 ("the") - 2 beats
    77.78,         # D#2 ("sound")
    92.50,         # F#2 ("That")
    103.83,        # G#2 ("saved")
    103.83,        # G#2 ("a")
    116.54,        # A#2 ("wretch")
    103.83, 103.83, # G#2 ("like") - 2 beats
    92.50          # F#2 ("me.")
]

c_major_scale = [
    ("C5", 523.25),  # High C
    ("B4", 493.88),  # B
    ("A4", 440.00),  # A
    ("G4", 392.00),  # G
    ("F4", 349.23),  # F
    ("E4", 329.63),  # E
    ("D4", 293.66),  # D
    ("C4", 261.63)   # Low C
]

jjb_scale = [
   ("G4", 392.00),  # G
   ("F4", 349.23),  # F
   ("E4", 329.63),  # E
   ("D4", 293.66),  # D
   ("C4", 261.63)   # Low C
]

jingle_bells_melody = [
    ("E4", 329.63, "Jin-"), ("E4", 329.63, "gle"), ("E4", 329.63, "bells"),       # Jingle bells, jingle bells
    ("E4", 329.63, "Jin-"), ("E4", 329.63, "gle"), ("E4", 329.63, "bells"),       # Jingle all the way
    ("E4", 329.63, "Jin"), ("G4", 392.00, "gle"), ("C4", 261.63, "all"),          # Oh what fun it is to ride
    ("D4", 293.66, "the"), ("E4", 329.63, "way"),                                   # In a one-horse open sleigh
    ("F4", 349.23, "Oh"), ("F4", 349.23, "what"), ("F4", 349.23, "fun"), ("F4", 349.23, "it"),  # In a one-horse
    ("F4", 349.23, "is"), ("E4", 329.63, "to"), ("E4", 329.63, "ride"),        # Open sleigh
    ("E4", 329.63, "In a"), ("E4", 329.63, "one"), ("D4", 293.66, "horse"), ("D4", 293.66, "o-"),         # Hey! Oh what fun
    ("E4", 329.63, "pen"), ("D4", 293.66, "sleigh"), ("G4", 392.00, "HEYs!")            # Fun it is
]


def play_tones():
    index = 0
    while True:
        distance = measure_distance()
        fraction = 1-(distance - 10.0)/70.0
        if fraction > 1.0:
            print(f"reset! (distance: {distance}, fraction: {fraction})")
            index = 0
            continue
        if fraction < 0.0:
            continue
        (note, frequency, lyric) = jingle_bells_melody[index]
        index = (index + 1) % len(jingle_bells_melody)
        # scale_index = int(fraction * len(jjb_scale))
        # (note, frequency) = jjb_scale[scale_index]
        print(f"{lyric} {note}, frequency: {frequency}, distance: {distance}")
        buzzer.freq(int(frequency/2.0))
        buzzer.duty_u16(30000)
        utime.sleep_ms(400)
        buzzer.duty_u16(0)

        # convert distance
        utime.sleep_ms(200)
        # frequency = map_distance_to_frequency(distance)
        # frequency = snap_to_black_keys(frequency)
        # if frequency > 156:  # Ignore frequencies too low to be valid
        #     # frequency = int(amazing_grace_frequencies[index])
        #     print(f"distance: {distance}, snap to ag2 frequency: {frequency}")
        #     # index = (index + 1) % len(amazing_grace_frequencies)
        #     buzzer.freq(frequency)
        #     buzzer.duty_u16(30000)
        #     utime.sleep_ms(200)
        #     buzzer.duty_u16(0)
        # else:
        #     utime.sleep_ms(200)  # Pause when out of ran


# Start distance measurement on Core 1
# _thread.start_new_thread(measure_distance, ())
# play_tones()

def play_scale():
    buzzer.duty_u16(30000)
    for freq in range(500, 10, -1):
        print(f"freq: {freq}")
        buzzer.freq(int(freq))
        utime.sleep_ms(10)
    buzzer.duty_u16(0)

def play_fast():
    buzzer.duty_u16(30000)
    while True:
        distance = measure_distance()
        fraction = (distance - 10.0)/70.0
        if fraction > 1.0 or fraction < 0.0:
            buzzer.duty_u16(0)
            print(f"reset (distance: {distance}, fraction: {fraction})")
            continue
        buzzer.duty_u16(30000)
        frequency = int(fraction * 500 + 20)
        buzzer.freq(frequency)
        utime.sleep_ms(20)

def two_tone(pin, frequency, duration_ms):
    if frequency < 400:
        bit_bang_tone(pin, frequency, duration_ms)
        return
    buzzer = machine.PWM(machine.Pin(pin))
    buzzer.duty_u16(30000)
    buzzer.freq(frequency)
    utime.sleep_ms(duration_ms)
    
# play_scale()
# play_fast()

def bit_bang_tone(pin, frequency, duration_ms):
    buzzer = Pin(pin, Pin.OUT)
    if frequency <= 0:
        utime.sleep_ms(duration_ms)  # Silence
        return

    period = 1 / frequency  # Period of the wave (seconds)
    half_period = period / 2  # Half the wave for HIGH and LOW (seconds)
    end_time = utime.ticks_add(utime.ticks_ms(), duration_ms)

    while utime.ticks_diff(end_time, utime.ticks_ms()) > 0:
        buzzer.high()
        utime.sleep(half_period)
        buzzer.low()
        utime.sleep(half_period)

def bit_banging_sweep(start_freq, end_freq, step, duration_ms):
    for freq in range(start_freq, end_freq - 1, -step):  # Sweep down
        print(f"Playing {freq} Hz")
        bit_bang_tone(buzzer, freq, duration_ms)

def two_tone_sweep(start_freq, end_freq, step, duration_ms):
    for freq in range(start_freq, end_freq - 1, -step):  # Sweep down
        print(f"Playing {freq} Hz")
        two_tone(15, freq, duration_ms)


# Run a frequency sweep
# two_tone_sweep(1000, 1, step=1, duration_ms=10)

def play_two_tone():
    while True:
        distance = measure_distance()
        fraction = (distance - 10.0)/70.0
        if fraction > 1.0 or fraction < 0.0:
            buzzer = machine.PWM(machine.Pin(15))
            buzzer.duty_u16(0)
            print(f"reset (distance: {distance}, fraction: {fraction})")
            continue
        frequency = int(fraction * 1000)
        print(f"distance: {distance}, frequency: {frequency}")
        two_tone(15, frequency, 20)

# play_two_tone()
# two_tone_sweep(1000, 1, step=1, duration_ms=10)




# Define the PIO program for generating a square wave
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def square_wave():
    wrap_target()
    pull(block)           # Wait until new data is available in FIFO
    mov(x, osr)           # Move the delay value into X register
    set(pins, 1)          # Set pin HIGH
    label("delay_high")
    jmp(x_dec, "delay_high")[15]  # Decrement X until it reaches 0
    set(pins, 0)          # Set pin LOW
    pull(block)           # Wait for next delay value
    mov(x, osr)           # Load next delay into X register
    label("delay_low")
    jmp(x_dec, "delay_low")[15]  # Decrement X until it reaches 0
    wrap()

# Function to calculate delay for a given frequency
def frequency_to_delay(frequency, pio_clock_hz=125_000_000):
    total_cycles = pio_clock_hz // frequency
    adjusted_cycles = (total_cycles // 2) // 16  # Subtract the extra delay from [15]
    
    if adjusted_cycles > 65535:
        raise ValueError("Frequency too low for this implementation")
    if adjusted_cycles < 1:
        raise ValueError("Frequency too high for this implementation")
    
    return adjusted_cycles


def test_fixed_frequency():
    buzzer = Pin(15, Pin.OUT)  # GPIO 15 for buzzer
    sm = rp2.StateMachine(0, square_wave, set_base=buzzer)

    sm.active(1)  # Start the PIO state machine
    while True:
        distance = measure_distance()
        fraction = (distance - 10.0)/70.0
        if fraction > 1.0 or fraction < 0.0:
            continue
        frequency = int(fraction * 1000)+60
        delay = frequency_to_delay(frequency)
        print(f"Delay for {frequency} Hz: {delay}")


        # Push delay values into the FIFO
        for _ in range(frequency//20+1):
            sm.put(delay)  # Send delay for HIGH
            sm.put(delay)  # Send delay for LOW
            # utime.sleep_ms(200)  # Let the tone play briefly

    sm.active(0)  # Stop the PIO state machine

test_fixed_frequency()