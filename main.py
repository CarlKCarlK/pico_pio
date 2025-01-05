import rp2
from machine import Pin
import time

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def sound():
    label("wait_for_nonzero")
    pull(block)             # Wait for an initial value from the FIFO
    mov(x, osr)             # Store the frequency in X
    jmp(not_x, "wait_for_nonzero")       # If x is zero, jump to "top"
    wrap_target()           # Start of the loop
    set(pins, 1)            # Set the pin high
    label("high_voltage_loop")
    jmp(x_dec, "high_voltage_loop") # Delay
    mov(x, osr)               # Reload the delay into Y
    set(pins, 0)            # Set the pin low
    label("low_voltage_loop")
    jmp(x_dec, "low_voltage_loop")  # Delay
    mov(x, osr)
    pull(noblock)           # If no value, copy x into osr
    jmp(not_x, "wait_for_nonzero")       # If x is zero, jump to "top"
    wrap()                  # End of the loop

def demo_sound():
    CLK_FREQ = 125_000_000  # 125 MHz
    BUZZER_PIN = 15 
    print("Hello, world7!")
    
    pio = rp2.PIO(0)
    pio.remove_program()
    sm = rp2.StateMachine(0, sound, set_base=Pin(BUZZER_PIN))

    print("PIO log sweep starting...")
    sm.active(1)  # Start the PIO state machine

    try:
        while True:
            for freq in range(100, 1000, 10):
                try:
                    half_period = int(CLK_FREQ / (2 * freq))
                    print(half_period)
                    sm.put(half_period)
                    time.sleep_ms(50)  # Add delay between frequencies
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

def main():
    demo_sound()

main()

