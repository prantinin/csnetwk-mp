from networking.message_parser import MessageParser
from game.battle_state import BattleState
import socket

# GLOBAL VARIABLES AND CONSTANTS
HOST = "127.0.0.1"  # Host IP address
PORT = 65432        # Port used by host

parser = MessageParser()

divider = "==========================================\n\n"
top_divider = "================== JOINER ================\n"
init_divider = "=============== INITIALIZATION ===========\n"
battle_setup_divider = "=============== BATTLE SETUP ===========\n"
your_turn_divider = "================== YOUR TURN ==============\n"
their_turn_divider = "================== OPPONENT'S TURN =======\n"



# FUNCTIONS

# Initialize battle setup
def init_battle():         
    pokemon = input("Choose your Pokemon: ")
    s_atk = input("How much special attack boost? ")
    s_def = input("How much special defense boost? ")

    return {
        "pokemon": pokemon,
        "s_atk": s_atk,
        "s_def": s_def
    }

# Start Battle Loop
def start_game(socket_obj, addr, state: BattleState):
    # dummy data
    attack_data = 20
    pokemon = "pikachu"
    last_attack = "Thunderbolt"
    pokemon_hp = 200
    defender_hp = 200
    damage = 20
    
    while not state.is_game_over():
        
        # JOINER ATTACK, HOST DEFEND
        if state.my_turn:
            
            #! WAITING_FOR_MOVE

            # You choosing attack move
            # pls remember to lower() pokemon moves from cv as well
            print(your_turn_divider)
            move_name = input("Choose your attack move: ").lower()
            my_move = {
                "message_type": "ATTACK_ANNOUNCE",
                "move_name": move_name,
                "sequence_number": state.next_sequence_number()
            }
            socket_obj.sendto(parser.encode_message(my_move).encode(), addr)

            # Awaiting opp def announcement
            print("\nAttack announcement sent. Awaiting defense announcement...")

            data, __ = socket_obj.recvfrom(1024)
            recvd_msg = parser.decode_message(data.decode())

            if recvd_msg["message_type"] == "DEFENSE_ANNOUNCE":
                state.receive_defense_announce()
                print("Opponent defense announcement received. Beginning damage calculation...\n")



                #! PROCESSING_TURN
                # Preparing calculation report
                remaining_health = pokemon_hp - damage
                state.record_local_calculation(remaining_health)

                # Status message following calculation confirmation
                effect = "super effective"  # example palang
                status_message = (f"{pokemon} used {last_attack}! It was {effect}!")

                # Send calculation report
                calcu_report = {
                    "message_type": "CALCULATION_REPORT",
                    "attacker": pokemon,
                    "move_used": last_attack,
                    "remaining_health": remaining_health,
                    "damage_dealt": damage,             
                    "defender_hp_remaining": defender_hp,
                    "status_message": status_message,
                    "sequence_number": state.next_sequence_number()
                }
                socket_obj.sendto(parser.encode_message(calcu_report).encode(), addr)
                print("Calculation report sent! Checking for discrepancies...")

                # Awaiting opp calculation confirmation
                data, __ = socket_obj.recvfrom(1024)
                recvd_msg = parser.decode_message(data.decode())

                if recvd_msg["message_type"] == "CALCULATION_CONFIRMATION":
                    #state.receive_calculation_report(
                    #        recvd_msg.get("remaining_health"),
                    #        recvd_msg.get("sequence_number")
                    #    )
                    print("All calculations similar! Turn end!")
                    state.switch_turn()




        # JOINER DEFEND, HOST ATTACK
        else: 

            #! WAITING_FOR_MOVE

            # Awaiting opp attack announce
            print(their_turn_divider)
            print("Waiting for opponent's move...\n")

            data, __ = socket_obj.recvfrom(1024)
            recvd_msg = parser.decode_message(data.decode())

            if recvd_msg["message_type"] == "ATTACK_ANNOUNCE":
                accepted = state.receive_attack_announce(attack_data)   # link to actual data later
                print(f"Opponent attack received: {accepted}")

                # Sending def announcement
                if accepted:
                    my_def_msg = parser.encode_message({
                        "message_type": "DEFENSE_ANNOUNCE",
                        "sequence_number": state.next_sequence_number()
                    })
                    socket_obj.sendto(my_def_msg.encode(), addr)
                    state.receive_defense_announce()
                    print("Defense announcement sent.\n")
                    
                    # Loop til calculations are confirmed
                    confirmed_calcu = False
                    while not confirmed_calcu:
                        


                        #! PROCESSING_TURN
                        # Receiving opp calculation report (compare later)
                        data, __ = socket_obj.recvfrom(1024)
                        recvd_msg = parser.decode_message(data.decode())
                        state.receive_calculation_report(recvd_msg, recvd_msg["sequence_number"])
                        state.receive_calculation_confirm()
                        
                        print(f"Received opponent calculation report:\n {recvd_msg}\n")
                        print("Beginning own damage calculation...")

                        # Preparing own calculation report
                        remaining_health = defender_hp - damage
                        opp_remaining_health = defender_hp - damage
                        state.record_local_calculation(remaining_health)

                        # Status message following calculation confirmation
                        effect = "super effective"  # example palang
                        status_message = (f"{pokemon} used {last_attack}! It was {effect}!")

                        # Send calculation report
                        calcu_report = {
                            "message_type": "CALCULATION_REPORT",
                            "attacker": pokemon,
                            "move_used": last_attack,
                            "remaining_health": pokemon_hp,
                            "damage_dealt": damage,             
                            "defender_hp_remaining": opp_remaining_health,
                            "status_message": status_message,
                            "sequence_number": state.next_sequence_number()
                        }
                        socket_obj.sendto(parser.encode_message(calcu_report).encode(), addr)
                        state.receive_calculation_confirm()
                        
                        print("Calculation report complete and sent to opponent.")
                        print("Comparing calculation reports...")

                        # Comparing calculation reports
                        confirmed_calcu = state.both_confirmed()

                        if confirmed_calcu:
                            print(f"Calculation reports similar: {confirmed_calcu}")
                            confirmed_msg = {
                                "message_type": "CALCULATION_CONFIRMATION",
                                "sequence_number": state.next_sequence_number()
                            }
                            socket_obj.sendto(parser.encode_message(confirmed_msg).encode(), addr)
                            state.switch_turn()
                            print(f"turn: {state.my_turn}")
                        else:
                            print(f"Calculation reports similar: {confirmed_calcu}")
                            print("Sending resolution request...")
                            res_req_msg = {
                                "message_type": "RESOLUTION_REQUEST",
                                "attacker": pokemon,
                                "move_used": last_attack,
                                "damage_dealt": damage,
                                "defender_hp_remaining": opp_remaining_health,
                                "sequence_number": state.next_sequence_number()
                            }
                            socket_obj.sendto(parser.encode_message(res_req_msg).encode(), addr)

                
            else:
                print(f"Unexpected message received:\n{recvd_msg}")
                


    #! GAME_OVER



# Initialize joiner
def joiner_handshake():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        
        # Joiner connects to host
        print(init_divider)
        print(f"[JOINER] Connected to host at {HOST}:{PORT}")
        print(f"[JOINER] Sending handshake request...\n")

        # Sending handshake request to host
        joiner_msg = "HANDSHAKE_REQUEST"
        joiner_response = parser.encode_message({"message_type": joiner_msg})
        s.sendto(joiner_response.encode(), (HOST, PORT))

        while True:
            data, addr = s.recvfrom(1024)
            host_msg = parser.decode_message(data.decode())
            message_type = host_msg.get("message_type")
            seed = host_msg.get("seed")

            # Host handshake response handling
            if message_type == "HANDSHAKE_RESPONSE":
                print(f"[JOINER] Host message received:\n{host_msg}\n")
                print("[JOINER] Handshake with host complete!\n\n")

                # Battle setup initiation from host
                print(battle_setup_divider)
                
                print("Initializing battle setup...")
                print("Awaiting host battle setup data...\n")

            elif message_type == "BATTLE_SETUP":
                host_msg = parser.decode_message(data.decode())
                print(f"\nBattle setup data received from Host:\n{host_msg}\n\n")

                # Sending host battle setup data
                poke_data = init_battle()
                host_response = parser.encode_message({
                    "message_type": "BATTLE_SETUP",
                    "battle_data": poke_data
                }) 
                s.sendto(host_response.encode(), addr)
                print("\nBattle setup data sent to Host. Battle initialization complete!\n\n")

                # Start battle loop
                battle_state = BattleState(is_host=False, seed=seed, verbose=True)
                start_game(s, addr, battle_state)

            else:
                print(f"[JOINER] Unexpected message type: {message_type}")



# MAIN
joiner_handshake()