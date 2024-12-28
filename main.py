from lcd1602 import LCD
from machine import Pin
import machine # type: ignore
import utime # type: ignore
import _thread
import math

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

def play_tones():
    while True:
        distance = measure_distance()
        fraction = 1-(distance - 10.0)/70.0
        if fraction < 0.0 or fraction > 1.0:
            continue
        index = int(fraction * len(jjb_scale))
        (note, frequency) = jjb_scale[index]
        print(f"{note}, frequency: {frequency}, distance: {distance}")
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
play_tones()
