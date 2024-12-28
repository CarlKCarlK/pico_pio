from lcd1602 import LCD
from machine import Pin
import machine
# import utime as utime
import utime
import random
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


# def tone(pin, frequency, duration_ms):
#     print(f"tone {frequency} {duration_ms}")
#     if frequency == 0:  # Pause
#         utime.sleep_ms(int(duration_ms))
#     else:
#         pin.freq(frequency)
#         pin.duty_u16(30_000)
#         utime.sleep_ms(int(duration_ms))
#         pin.duty_u16(0)


def song(melody):
    # Initialize PWM on GPIO pin 15
    # Play the melody
    for note, duration_beats in melody:
        frequency = NOTE_FREQUENCIES[note]
        tone(buzzer, frequency, duration_beats)
        utime.sleep_ms(int(beat_duration_ms * 0.1))  # Short pause between notes

def you_lose(message):
    lcd.clear()
    lcd.write(0, 0, "You lose!")
    lcd.write(0, 1, message)
    # song(jingle_bells_melody) 
    song(one_melody)

def add_pins(colors, pins, index):
    while True:
        if connected(pins[index]):  # Pin at the given index
            break
        if any(connected(pin) for pin in pins[index:]):  # Pins before the given index
            return False
        utime.sleep(0.1)
    return True

def monitor_removal(colors_mission, pins_mission, i):
    while True:
        lcd.write(0, 0, f"tick {i}")
        for j in range(len(pins_mission)):
            pin_j = pins_mission[j]
            if j < i:
                if connected(pin_j):
                    return False
            elif j > i:
                if disconnected(pin_j):
                    return False
            else:
                if disconnected(pin_j):
                    return True
        utime.sleep(0.1)

def connected(pin):
    return pin.value() == 0

def disconnected(pin):
    return pin.value() == 1

def connected_str(pin):
    return "connected" if connected(pin) else "disconnected"

def permutation(n):
    lst = []
    for i in range(n):
        j = random.randint(0, i)
        lst.append(None)
        for k in range(i, j, -1):
            lst[k] = lst[k - 1]
        lst[j] = i
    return lst



# Map distance to frequency
def map_distance_to_frequency(distance_cm):
    if distance_cm > 100.0:
        return 0  # Silence for distances > 100
    else:
        # Map 3-60 cm to 200-1000 Hz range
        return int(200.0 + ((distance_cm - 3.0) * (800.0 / (60.0 - 3.0))))

# Measure distance (runs on Core 1)


def measure_distance():
    global shared_distance

    TRIG = machine.Pin(17, machine.Pin.OUT)
    ECHO = machine.Pin(16, machine.Pin.IN)

    while True:
        TRIG.low()
        utime.sleep_us(2)
        TRIG.high()
        utime.sleep_us(10)
        TRIG.low()

        # Timeout for the echo start
        start_time = utime.ticks_us()
        while not ECHO.value():
            if utime.ticks_diff(utime.ticks_us(), start_time) > 100000:  # 100 ms timeout
                shared_distance[0] = 200
                break

        time1 = utime.ticks_us()
        while ECHO.value():
            if utime.ticks_diff(utime.ticks_us(), time1) > 100000:  # 100 ms timeout
                shared_distance[0] = 200
                break

        time2 = utime.ticks_us()
        duration = utime.ticks_diff(time2, time1)
        distance_cm = float(duration) * 340.0 / 2.0 / 10000.0


        # Update the shared distance with the smoothed value
        shared_distance[0] = distance_cm

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
    return round(snapped_freq)

def play_tones():
    while True:
        distance = shared_distance[0]
        frequency = map_distance_to_frequency(distance)
        frequency = snap_to_black_keys(frequency)
        print(f"distance: {distance}, snap to black frequency: {frequency}")
        if frequency > 50:  # Ignore frequencies too low to be valid
            buzzer.freq(frequency)
            buzzer.duty_u16(30000)
            utime.sleep_ms(200)
            buzzer.duty_u16(0)
        else:
            utime.sleep_ms(200)  # Pause when out of ran


# Start distance measurement on Core 1
_thread.start_new_thread(measure_distance, ())
play_tones()
