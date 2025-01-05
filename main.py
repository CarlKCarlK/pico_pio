import rp2
from machine import Pin
import time

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def sound():
    # cmk we don't need x, we can just use osr
    label("top")
    pull(block)            # Wait for an initial value from the FIFO
    mov(x, osr)             # Store the frequency in X
    jmp(not_x, "top")       # If x is zero, jump to "top"
    wrap_target()           # Start of the loop
    mov(y, x)               # Reload the delay into Y
    set(pins, 1)            # Set the pin high
    label("high_loop")
    jmp(y_dec, "high_loop") # Delay
    mov(y, x)               # Reload the delay into Y
    set(pins, 0)            # Set the pin low
    label("low_loop")
    jmp(y_dec, "low_loop")  # Delay
    pull(noblock)           # If no value, copy x into osr
    mov(x, osr)
    jmp(not_x, "top")       # If x is zero, jump to "top"
    wrap()                  # End of the loop

def main():
    CLK_FREQ = 125_000_000  # 125 MHz
    BUZZER_PIN = 15 
    print("Hello, world6!")
    
    pio = rp2.PIO(0)
    pio.remove_program()
    sm = rp2.StateMachine(0, sound, set_base=Pin(BUZZER_PIN))

    print("PIO log sweep starting...")
    sm.active(1)  # Start the PIO state machine

    try:
        while True:
            for freq in range(100, 1000):
                try:
                    half_period = int(CLK_FREQ / (2 * freq))
                    print(half_period)
                    sm.put(half_period)
                    time.sleep_ms(25)  # Add delay between frequencies
                except Exception as e:
                    print(f"Error during frequency change: {e}")
                    continue
    except KeyboardInterrupt:
        sm.active(0)
        print("Sweep stopped.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        sm.active(0)  # Ensure state machine is stopped

main()

