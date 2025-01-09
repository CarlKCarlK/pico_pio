# import backup
import sound



# @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
# def distance():
#     # x is the last value sent. Initialize it to 
#     # u32::MAX which means 'echo timeout'
#     # (Set x to u32::MAX by subtracting 1 from 0)
#     set(x, 0)
#     label("unused")
#     jmp(x_dec, "unused")

#     # Read the max echo wait into osr.
#     pull()
#     # set(x, 400000)
#     # mov(osr, x)
    
#     # Take a measurement loop
#     wrap_target()

#     # Generate 10μs trigger pulse (1250 cycles at 125MHz)
#     set(pins, 1)                    # Set trigger pin to high voltage
#     set(y, 25)                      # Setup loop counter (25 × 50 cycles = 1250)
#     label("trigger_pulse_loop")
#     nop() [31]                      # Delay 32 cycles
#     jmp(y_dec, "trigger_pulse_loop") [17]  # 18 cycles (50 total per iteration)

#     set(pins, 0)                    # Set trigger pin to low voltage
    
#     wait(1, pin, 0)                 # Wait for echo pin to be high voltage
#     mov(y, osr)                     # Load max echo wait into y

#     # Count down the echo wait
#     label("measure_echo_loop")
#     jmp(pin, "echo_active")          # if echo voltage is high continue count down
#     jmp("measurement_complete")      # if echo voltage is low, measurement is complete
#     label("echo_active")
#     jmp(y_dec, "measure_echo_loop")  # Continue counting down unless timeout
    
    
#     # y tells where the echo countdown stopped. It
#     # will be u32::MAX if the echo timed out.
#     label("measurement_complete")
#     jmp(x_not_y, "send_result")     # if measurement is different, then sent it.
#     jmp("cooldown_cycle")           # If measurement is the same, don't send.
#     # Send the measurement
#     label("send_result")
#     mov(isr, y)                     # Store result in ISR
#     push()                          # Send to FIFO
#     mov(x, y)                       # Save the result in x
    
#     # Cool down period before next measurement
#     # about 30 ms (10 times 400,000 / 150,000,000)
#     label("cooldown_cycle")
#     mov(y, osr)                     # Load cool down counter
#     label("cooldown_loop")
#     jmp(y_dec, "cooldown_loop") [9] # Wait before next measurement
#     wrap()                          # Restart the measurement loop

# def demo_distance():
#     print("Hello, distance2!")
    
#     pio1 = rp2.PIO(1)
#     pio1.remove_program()

#     trigger = Pin(TRIGGER_PIN, Pin.OUT)
#     echo = Pin(ECHO_PIN, Pin.IN)
#     distance_state_machine = rp2.StateMachine(4, distance, set_base=trigger, in_base=echo, jmp_pin=echo)

#     print("Distance ...")
#     distance_state_machine.active(1)  # Start the PIO state machine
#     distance_state_machine.put(START_CYCLES)

#     try:
#         while True:
#                 end_cycles = distance_state_machine.get()
#                 distance_cm = end_cycles_to_distance_cm(end_cycles)
#                 print(f"Distance: {distance_cm} cm, end_cycles: {end_cycles}")
#     except KeyboardInterrupt:
#         distance_state_machine.active(0)
#         print("Distance stopped.")
#     except Exception as e:
#         print(f"Unexpected error: {e}")
#     finally:
#         distance_state_machine.active(0)  # Ensure state machine is stopped

# def end_cycles_to_distance_cm(end_cycles):
#     if end_cycles == 0xFFFFFFFF:
#         return None
#     distance_cm = (START_CYCLES - end_cycles) * CM_PER_LOOP
#     return distance_cm

# def distance_to_frequency(distance):
#     return F_LOW * 2.0** ((distance / D_MAX) * N_OCTAVES)



# def make_music():
#     print("Hello, music!")
    
#     pio0 = rp2.PIO(0)
#     pio0.remove_program()
#     sound_state_machine = rp2.StateMachine(0, sound, set_base=Pin(BUZZER_PIN))

#     pio1 = rp2.PIO(1)
#     pio1.remove_program()
#     trigger = Pin(TRIGGER_PIN, Pin.OUT)
#     echo = Pin(ECHO_PIN, Pin.IN)
#     distance_state_machine = rp2.StateMachine(4, distance, set_base=trigger, in_base=echo, jmp_pin=echo)


#     print("0Music starting...")
#     sound_state_machine.active(1)
#     print("1Music starting...")
#     distance_state_machine.active(1)
#     print("2Music starting...")
#     distance_state_machine.put(START_CYCLES)

#     try:
#         while True:
#             # print("getting distance")
#             end_cycles = distance_state_machine.get()
#             print("end_cycles: ", end_cycles)
#             distance_cm = end_cycles_to_distance_cm(end_cycles)
#             if distance_cm is None:
#                 sound_state_machine.put(0)
#             else:
#                 freq = distance_to_frequency(distance_cm)
#                 half_period = int(CLOCK_FREQUENCY / (2 * freq))
#                 sound_state_machine.put(half_period)
#     except KeyboardInterrupt:
#         sound_state_machine.active(0)
#         print("music stopped.")
#     except Exception as e:
#         print(f"Unexpected error: {e}")
#     finally:
#         sound_state_machine.active(0)  # Ensure state machine is stopped

# def main():
#     print("main4")
#     demo_sound()
#     # demo_distance()
#     # make_music()

# # main()

