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

    # Generate 10μs trigger pulse (1500 cycles at 150MHz)
    set(pins, 1)                    # Set trigger pin to high voltage
    set(y, 30)                      # Setup loop counter (30 × 50 cycles = 1500)
    label("trigger_pulse_loop")
    nop() [31]                      # Delay 32 cycles
    jmp(y_dec, "trigger_pulse_loop") [17]  # 18 cycles (50 total per iteration)
    set(pins, 0)                    # Set trigger pin to low voltage
    
    # Count down the echo wait
    wait(1, pin, 0)                 # Wait for echo pin to be high voltage
    mov(y, osr)                     # Load max echo wait into y
    label("measure_echo_loop")
    jmp(pin, "echo_active")          # if echo voltage is high continue count down
    jmp("measurement_complete")      # if echo voltage is low, measurement is complete
    label("echo_active")
    jmp(y_dec, "measure_echo_loop")  # Continue counting down unless timeout
    
    
    # y tells where the echo countdown stopped. It
    # will be u32::MAX if the echo timed out.
    label("measurement_complete")
    jmp(x_not_y, "send_result")     # if measurement is different, then sent it.
    jmp("cooldown")           # If measurement is the same, don't send.
    # Send the measurement
    label("send_result")
    mov(isr, y)                     # Store result in ISR
    push()                          # Send to FIFO
    mov(x, y)                       # Save the result in x
    
    # Cool down period before next measurement
    label("cooldown")
    wait(0, pin, 0)                 # Wait for echo pin to be low
    wrap()                          # Restart the measurement loop
