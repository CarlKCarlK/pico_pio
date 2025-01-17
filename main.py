# import backup
# import sound
# import distance_demo
import debug_demo


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

