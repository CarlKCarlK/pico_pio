import rp2

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def sound():
    # Rest until a new tone is received.
    label("resting")
    pull(block)                     # Wait for a new delay value, keep it in osr.
    mov(x, osr)                     # Copy the delay into X.
    jmp(not_x, "resting")           # If new delay is zero, keep resting.

    # Play the tone until a new delay is received.
    wrap_target()                   # Start of the main loop.

    set(pins, 1)                    # Set the buzzer to high voltage.
    label("high_voltage_loop")
    jmp(x_dec, "high_voltage_loop") # Delay

    set(pins, 0)                    # Set the buzzer to low voltage.
    mov(x, osr)                     # Load the half period into X.
    label("low_voltage_loop")
    jmp(x_dec, "low_voltage_loop")  # Delay

    # Read any new delay value. If none, keep the current delay.
    mov(x, osr)                     # set x, the default value for "pull(nonblock)"
    pull(noblock)                   # Read a new delay value or use the default.

    # If the new delay is zero, rest. Otherwise, continue playing the tone.
    mov(x, osr)                     # Copy the delay into X.
    jmp(not_x, "resting")           # If X is zero, rest.
    wrap()                          # Continue playing the sound.

