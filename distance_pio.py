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

    # # Initialize Y to 500
    # set(y, 0)          # Clear y (initialize to 0)
    # mov(isr, y)        # Clear ISR (initialize to 0)
    # set(y, 15)         # Load higher 5 bits (15 = 0b01111) into y
    # in_(y, 5)          # Shift ISR left by 5 bits and insert y (ISR = 0b00001111)
    # set(y, 20)         # Load lower 5 bits (20 = 0b10100) into y
    # in_(y, 5)          # Shift ISR left by 5 bits and insert y (ISR = 0b0111110100 = 500)
    # mov(y, isr)        # Move final value (500) from ISR to y


    # Generate 10μs trigger pulse (4 cycles at 343_000Hz)
    set(pins, 1)[3]                 # Set trigger pin to high voltage
    set(pins, 0)                    # Set trigger pin to low voltage
    
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
    mov(isr, y)                     # Store result in ISR
    push()                          # Send to FIFO
    mov(x, y)                       # Save the result in X
    
    # Cool down period before next measurement
    label("cooldown")
    wait(0, pin, 0)                 # Wait for echo pin to be low
    wrap()                          # Restart the measurement loop
