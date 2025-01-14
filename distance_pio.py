import rp2

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def distance():
    # X is the last value sent. Initialize it to 
    # u32::MAX which means 'echo timeout'
    # (Set X to u32::MAX by subtracting 1 from 0)
    set(x, 0)
    label("subtraction_trick")
    jmp(x_dec, "subtraction_trick")

    # Read the max echo wait into OSR.
    pull() # same as pull(block)
    
    # Main loop
    wrap_target()

    # Generate 10μs trigger pulse (4 cycles at 343_000Hz)
    set(pins, 0b1)[3]                # Set trigger pin to high, add delay of 3
    set(pins, 0b0)                   # Set trigger pin to low voltage
    
    # When the trigger goes high, start counting down until it goes low
    wait(1, pin, 0)                 # Wait for echo pin to be high voltage
    mov(y, osr)                     # Load max echo wait into Y

    label("measure_echo_loop")
    jmp(pin, "echo_active")         # if echo voltage is high continue count down
    jmp("measurement_complete")     # if echo voltage is low, measurement is complete
    label("echo_active")
    jmp(y_dec, "measure_echo_loop") # Continue counting down unless timeout

    # Y tells where the echo countdown stopped. It
    # will be u32::MAX if the echo timed out.
    label("measurement_complete")
    jmp(x_not_y, "send_result")     # if measurement is different, then sent it.
    jmp("cooldown")                 # If measurement is the same, don't send.
    # Send the measurement
    label("send_result")
    mov(isr, y)                    # Store measurement in ISR
    push()                         # Output ISR
    mov(x, y)                      # Save the measurement in X
    
    # Cool down period before next measurement
    label("cooldown")
    wait(0, pin, 0)                 # Wait for echo pin to be low
    wrap()                          # Restart the measurement loop
    