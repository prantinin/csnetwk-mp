from networking.message_parser import MessageParser
from game.battle_state import BattleState

import socket

# GLOBAL VARIABLES AND CONSTANTS
HOST = "127.0.0.1"  # Host IP address
PORT = 65432        # Port used by host

divider = "==========================================\n\n"
top_divider = "================== JOINER ================\n\n"
parser = MessageParser()



# FUNCTIONS

# Initialize battle setup
def init_battle():         
    pokemon = input("Choose your Pokemon: ")
    s_atk = input("How much special attack boost? ")
    s_def = input("How much special defense boost? ")

    return {
        "pokemon_name": pokemon,
        "stat_boosts": {
            "special_attack_uses": s_atk, 
            "special_defense_uses": s_def
        }
    }


# Start Battle
def start_battle(socket_obj, addr, state: BattleState):
    while not state.is_game_over():

        # JOINER DEFEND, HOST ATTACK
        if state.my_turn:

            # Awaiting host attack announce
            print(f"Waiting for opponent's move...\n")
            
            data, __ = socket_obj.recvfrom(1024)
            recvd_msg = parser.decode_message(data.decode())

            attack_data = 20    # sample attack
            if recvd_msg["message_type"] == "ATTACK_ANNOUNCE":
                accepted = state.receive_attack_announce(attack_data)   # link to actual data later

                # Send joiner defense announce
                if accepted:
                    host_msg = parser.encode_message({
                        "message_type": "DEFENSE_ANNOUNCE",
                        "sequence_number": state.next_sequence_number()
                    })
                    socket_obj.sendto(host_msg.encode(), addr)

                confirmed = False
                while not confirmed:

                    # Joiner computes damage taken
                    incoming = attack_data   # link to actual data later
                    remaining_health = state.opponent_pokemon["hp"] - incoming
                    state.record_local_calculation(remaining_health)

                    # Send calculation report
                    report = parser.encode_message({
                        "message_type": "CALCULATION_REPORT",
                        "remaining_health": remaining_health,
                        "sequence_number": state.next_sequence_number()
                    })
                    socket_obj.sendto(report.encode(), addr)

                    # Awaiting host confirmation
                    data, __ = socket_obj.recvfrom(1024)
                    recvd_msg = parser.decode_message(data.decode())

                    if recvd_msg["message_type"] == "CALCULATION_CONFIRMATION":
                        state.receive_calculation_confirm()
                        state.send_calculation_confirm()

                        # Check if both confirmed
                        confirmed = state.both_confirmed()

                        if confirmed:
                            pass  # proceed to next turn
                        else:
                            print("Players calculations not yet confirmed.")
                            report["message_type"] = "RESOLUTION_REQUEST"
                            encoded_report = parser.encode_message(report)
                            socket_obj.sendto(encoded_report.encode(), addr)
                
                # Turn switch after both confirmed
                print(status_message)
                print(divider)
                state.switch_turn()
            

        # JOINER ATTACK, HOST DEFEND
        else:
            
            # Joiner choosing attack move
            # pls remember to lower pokemon moves from cv as well
            move = input("Choose your attack move: ").lower()
            my_move = parser.encode_message({
                "message_type": "ATTACK_ANNOUNCE",
                "move_name": move,
                "sequence_number": state.next_sequence_number()
            })
            socket_obj.sendto(my_move.encode(), addr)

            # Waiting for joiner defense response
            data, __ = socket_obj.recvfrom(1024)
            recvd_msg = parser.decode_message(data.decode())

            if recvd_msg["message_type"] == "DEFENSE_ANNOUNCE":
                confirmed = False
                while not confirmed:

                    # Joiner computes damage
                    # damage example palang
                    damage = 20  # example palang
                    remaining_health = state.my_pokemon["hp"] - damage
                    state.record_local_calculation(remaining_health)

                    # Status message following calculation confirmation
                    effect = "super effective"  # example palang
                    status_message = (f"{state.my_pokemon} used {move}! It was {effect}!\n")

                    # Send joiner's calculation report
                    report = {
                        "message_type": "CALCULATION_REPORT",
                        "attacker": state.my_pokemon,
                        "move_used": state.last_attack,
                        "remaining_health": remaining_health,
                        "damage_dealt": 10,  # example palang
                        "defender_hp_remaining": None, # state.opponent_pokemon["hp"],
                        "status_message": status_message,
                        "sequence_number": state.next_sequence_number()
                    }
                    encoded_report = parser.encode_message(report)
                    socket_obj.sendto(encoded_report.encode(), addr)
                    
                    # Awaiting host confirmation
                    data, __ = socket_obj.recvfrom(1024)
                    recvd_msg = parser.decode_message(data.decode())

                    if recvd_msg["message_type"] == "CALCULATION_CONFIRMATION":
                        state.receive_calculation_report(
                            recvd_msg["remaining_health"],
                            recvd_msg["sequence_number"]
                        )
                        state.receive_calculation_confirm()
                        state.send_calculation_confirm()

                        # Check if both confirmed
                        confirmed = state.both_confirmed()

                        if confirmed:
                            pass  # proceed to next turn
                        else:
                            print("Players calculations not yet confirmed.")
                            report["message_type"] = "RESOLUTION_REQUEST"
                            encoded_report = parser.encode_message(report)
                            socket_obj.sendto(encoded_report.encode(), addr)


                # Turn switch after both confirmed
                print(status_message)
                print(divider)
                state.switch_turn()

            else:
                pass  # handle unexpected message types if needed
    
    print(f"Congratulations, {state.winner}! You've won!")
    print("=============== GAME OVER! =================")

# Initialize joiner
def joiner_handshake():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        
        # Joiner connects to host
        print(divider)
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

            # Host handshake response handling
            if message_type["message_type"] == "HANDSHAKE_RESPONSE":
                print(f"[JOINER] Host message received:\n{host_msg}\n")
                print(f"[JOINER] Handshake with host complete!")
                print("\n")
            elif message_type["message_type"] == "BATTLE_SETUP":
                print(top_divider)
                
                # Battle setup initiation from host
                print(f"Initializing battle setup...\n")
                host_msg = parser.decode_message(data.decode())
                print(f"\nBattle setup data received from Host:\n{host_msg}\n")

                # Sending joiner battle setup data
                poke_data = init_battle()
                host_response = {
                    "message_type": "BATTLE_SETUP",
                    "battle_data": poke_data
                }
                s.sendto(host_response.encode(), addr)

                # Starting battle loop
                start_battle(s, addr, BattleState(is_host=False, seed=host_msg["seed"].get("seed"), verbose=True))

            else:
                break
            
        else:
            print(f"[JOINER] Unexpected message type: {message_type}")



# MAIN
joiner_handshake()