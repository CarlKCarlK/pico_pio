from lcd1602 import LCD
from machine import Pin
import machine
import utime as time
import random



def tone(pin,frequency,duration):
    pin.freq(frequency)
    pin.duty_u16(30000)
    time.sleep_ms(duration)
    pin.duty_u16(0)

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

# Tempo settings
BPM = 200  # Beats per minute; adjust this value to control the tempo
beat_duration_ms = 60000 / BPM  # Duration of a single beat in milliseconds

def tone(pin, frequency, duration_beats):
    duration_ms = duration_beats * beat_duration_ms
    if frequency == 0:  # Pause
        time.sleep_ms(int(duration_ms))
    else:
        pin.freq(frequency)
        pin.duty_u16(30_000)
        time.sleep_ms(int(duration_ms))
        pin.duty_u16(0)


def song(melody):
    # Initialize PWM on GPIO pin 15
    # Play the melody
    for note, duration_beats in melody:
        frequency = NOTE_FREQUENCIES[note]
        tone(buzzer, frequency, duration_beats)
        time.sleep_ms(int(beat_duration_ms * 0.1))  # Short pause between notes

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
        time.sleep(0.1)
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
        time.sleep(0.1)

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

def game():
    pins_numbers = [19, 18, 17, 16]
    colors = ["blue", "red", "green", "yellow"]
    pins = [Pin(pin_number, Pin.IN, Pin.PULL_UP) for pin_number in pins_numbers]
    holes = [50-i for i in range(len(pins))]

    lcd.clear()
    lcd.write(0,0,"remove any wires")
    lcd.write(0,1,f"{min(holes)} to {max(holes)} to gnd")

    # Wait until all wires are removed
    while any(connected(pin) for pin in pins):
        time.sleep(0.1)

    for index in range(len(pins)):
        lcd.clear()
        lcd.write(0, 0, f"Add {colors[index]}")
        lcd.write(0, 1, f"from {holes[index]} to gnd")
        if not add_pins(colors, pins, index):
            you_lose("Pin too early")
            return

    # Confirm that the user has connected all wires
    # if not, the user loses the game
    if any(disconnected(pin) for pin in pins):
        you_lose("Wires missing")
        return


    # random permutation of the pins
    random.seed(time.ticks_us())
    mission = permutation(len(pins))
    colors_mission = [colors[i] for i in mission]
    pins_mission = [pins[i] for i in mission]

    lcd.clear()
    lcd.write(0, 0, "Your mission...")
    time.sleep(5)
    for color in colors_mission:
        lcd.clear()
        lcd.write(0, 0, f"+/- {color}")
        time.sleep(1)
    lcd.clear()
    lcd.write(0, 0, "Begin:")

    for i in range(len(pins_mission)):
        if not monitor_removal(colors_mission, pins_mission, i):
            you_lose("Wrong wire")
            return
 

    lcd.clear()
    lcd.write(0,0,"Safe!")
    time.sleep(2)
    return

def main():
    while True:
        game()
        lcd.clear()
        lcd.write(0, 0, "Resetting...")
        time.sleep(2)

main()
