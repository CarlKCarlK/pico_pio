from lcd1602 import LCD
from machine import Pin
import machine
import utime as time



def tone(pin,frequency,duration):
    print("tone", pin,frequency,duration)
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

def you_lose():
    lcd.clear()
    lcd.write(0, 0, "You lose!")
    song(one_melody)

def add_pins(pin_objects, index):
    while True:
        if pin_objects[index].value() == 0:  # Pin at the given index
            break
        if any(pin.value() == 0 for pin in pin_objects[:index]):  # Pins before the given index
            you_lose()
            return
        time.sleep(0.1)

def main():

    # Define the GPIO pins to monitor
    pins_to_monitor = [16, 17, 18, 19]

    # Initialize each pin as an input with an internal pull-up resistor
    pin_objects = [Pin(pin_num, Pin.IN, Pin.PULL_UP) for pin_num in pins_to_monitor]

    lcd.clear()
    lcd.write(0,0,"remove any wires")
    lcd.write(0,1,"47 to 50 to gnd")

    # Wait until all wires are removed
    while any(pin.value() == 0 for pin in pin_objects):
        time.sleep(0.1)

    lcd.clear()
    lcd.write(0,0,"Add blue")
    lcd.write(0,1,"from 47 to gnd")
    add_pins(pin_objects, 3)

    lcd.clear()
    lcd.write(0,0,"Add red")
    lcd.write(0,1,"from 48 to gnd")
    add_pins(pin_objects, 2)

    lcd.clear()
    lcd.write(0,0,"Add green")
    lcd.write(0,1,"from 49 to gnd")
    add_pins(pin_objects, 1)

    lcd.clear()
    lcd.write(0,0,"Add yellow")
    lcd.write(0,1,"from 50 to gnd")
    add_pins(pin_objects, 0)


    lcd.clear()
    lcd.write(0,0,"End of program")


    # while True:
    #     for pin in pin_objects:
    #         if pin.value() == 0:
    #             print(f"GPIO {pin} is connected (LOW).")
    #         else:
    #             print(f"GPIO {pin} is disconnected (HIGH).")
    #     time.sleep(1)  # Delay to prevent excessive printing

main()
