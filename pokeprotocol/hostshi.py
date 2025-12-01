# HOSTSHI# host
from networking.message_parser import MessageParser
from game.battle_state import BattleState

import socket
import random
import time


# GLOBAL VARIABLES AND CONSTANTS
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

parser = MessageParser()
divider = "========================================\n"
top_divider = "================== HOST ================\n"



# FUNCTIONS

# Initialize battle setup
def init_battle():
    valid_com = False
    
    while not valid_com:
        comms = input("What communication mode would you like? (P2P/BROADCAST) ")
        comms = comms.upper()
        if comms == "P2P" or comms == "BROADCAST":
            valid_com = True
        else:
            print(f"Please choose only between the two avail. modes:>") 
            
    pokemon = input("Choose your Pokemon: ")
    s_atk = input("How much special attack boost? ")
    s_def = input("How much special defense boost? ")

    return {
        "communication_mode": comms,
        "pokemon_name": pokemon,
        "stat_boosts": {
            "special_attack_uses": int(s_atk), 
            "special_defense_uses": int(s_def)
        }
    }


# Start Battle
def start_battle(socket_obj, addr, state: BattleState):
    while not state.is_game_over():


        # HOST ATTACK, JOINER DEFEND
        if state.my_turn:
            
            # Host choosing attack move
            # pls remember to lower pokemon moves from cv as well
            move = input("Choose your attack move: ").lower()
            my_move = {
                "message_type": "ATTACK_ANNOUNCE",
                "move_name": move,
                "sequence_number": state.next_sequence_number()
            }
            socket_obj.sendto(parser.encode_message(my_move), addr)

            # Waiting for joiner defense response
            try:
                data, __ = socket_obj.recvfrom(1024)
            except socket.timeout:
                print("[HOST] Timeout waiting for DEFENSE_ANNOUNCE. Ending battle.")
                break

            recvd_msg = parser.decode_message(data)


            if recvd_msg["message_type"] == "DEFENSE_ANNOUNCE":

                # inform state that defense announce was received -> move to PROCESSING_TURN
                state.receive_defense_announce()

                confirmed_calcu = False
                while not confirmed_calcu:

                    # dummy data while waiting for other functions
                    pokemon = "pikachu"
                    last_attack = "Thunderbolt"
                    pokemon_hp = 200
                    damage = 20

                    # Host computes damage
                    remaining_health = pokemon_hp - damage
                    state.record_local_calculation(remaining_health)

                    # Status message following calculation confirmation
                    effect = "super effective"  # example palang
                    status_message = (f"{pokemon} used {last_attack}! It was {effect}!\n")

                    # Send calculation report
                    calcu_report = {
                        "message_type": "CALCULATION_REPORT",
                        "attacker": pokemon,
                        "move_used": last_attack,
                        "remaining_health": remaining_health,
                        "damage_dealt": damage,             
                        "defender_hp_remaining": defender_hp_after,
                        "status_message": status_message,
                        "sequence_number": state.next_sequence_number()
                    }
                    socket_obj.sendto(parser.encode_message(calcu_report), addr)
                    
                    # Awaiting joiner confirmation or report
                    try:
                        data, __ = socket_obj.recvfrom(1024)
                    except socket.timeout:
                        print("[HOST] Timeout waiting for calculation confirmation/report. Ending battle.")
                        return

                    recvd_msg = parser.decode_message(data)

                    if recvd_msg["message_type"] == "CALCULATION_CONFIRMATION":
                        state.receive_calculation_report(
                            recvd_msg.get("remaining_health"),
                            recvd_msg.get("sequence_number")
                        )
                        state.send_calculation_confirm()

                        # send an actual network confirmation message so the opponent is aware
                        confirm_msg = {
                            "message_type": "CALCULATION_CONFIRMATION",
                            "remaining_health": remaining_health,
                            "sequence_number": state.next_sequence_number()
                        }
                        socket_obj.sendto(parser.encode_message(confirm_msg), addr)

                        # Check if both confirmed
                        confirmed_calcu = state.both_confirmed()

                        if confirmed_calcu:
                            pass  # proceed to next turn 
                        else:
                            print("Players calculations not yet confirmed.")
                            resolution_request = {
                                "message_type": "RESOLUTION_REQUEST",
                                "attacker": pokemon,
                                "move_used": last_attack,
                                "damage_dealt": damage,
                                "defender_hp_remaining": defender_hp_after,
                                "sequence_number": state.next_sequence_number()
                            }
                            
                            socket_obj.sendto(parser.encode_message(resolution_request), addr)


                # Turn switched by both_confirmed()
                print(status_message)
                print(divider)


            else:
                pass  # handle unexpected message types if needed
            

        # HOST DEFEND, JOINER ATTACK
        else:

            # Awaiting joiner attack announce
            print(f"Waiting for opponent's move...\n")
            
            try:
                data, __ = socket_obj.recvfrom(1024)
            except socket.timeout:
                print("[HOST] Timeout waiting for ATTACK_ANNOUNCE. Ending battle.")
                break

            recvd_msg = parser.decode_message(data)

            # dummy data while waiting for other functions
            pokemon = "pikachu"
            last_attack = "Thunderbolt"
            pokemon_hp = 200
            damage = 20

            if recvd_msg["message_type"] == "ATTACK_ANNOUNCE":
                accepted = state.receive_attack_announce(recvd_msg)   # store attack data

                # Send host defense announce
                if accepted:
                    host_msg = {
                        "message_type": "DEFENSE_ANNOUNCE",
                        "sequence_number": state.next_sequence_number()
                    }
                    socket_obj.sendto(parser.encode_message(host_msg), addr)

                    # notify state that defense announce was processed (transition)
                    state.receive_defense_announce()

                confirmed = False
                while not confirmed:

                    # Host computes damage taken
                    remaining_health = pokemon_hp - damage   # link to actual data later
                    state.record_local_calculation(remaining_health)

                    # Status message following calculation confirmation
                    effect = "super effective"  # example palang
                    status_message = (f"{pokemon} used {last_attack}! It was {effect}!\n")

                    # Send calculation report
                    defender_hp_after = None
                    if state.opponent_pokemon is not None:
                        defender_hp_after = state.opponent_pokemon.get("hp")

                    calcu_report = {
                        "message_type": "CALCULATION_REPORT",
                        "attacker": pokemon,
                        "move_used": last_attack,
                        "remaining_health": remaining_health,
                        "damage_dealt": damage,
                        "defender_hp_remaining": defender_hp_after,
                        "status_message": status_message,
                        "sequence_number": state.next_sequence_number()
                    }
                    socket_obj.sendto(parser.encode_message(calcu_report), addr)

                    # Awaiting opponent confirmation
                    try:
                        data, __ = socket_obj.recvfrom(1024)
                    except socket.timeout:
                        print("[HOST] Timeout waiting for calculation confirmation/report. Ending battle.")
                        return

                    recvd_msg = parser.decode_message(data)

                    if recvd_msg["message_type"] == "CALCULATION_CONFIRMATION":
                        # update opponent calculation if provided
                        if "remaining_health" in recvd_msg and "sequence_number" in recvd_msg:
                            state.receive_calculation_report(
                                recvd_msg.get("remaining_health"),
                                recvd_msg.get("sequence_number")
                            )

                        # mark local confirm and send actual network confirmation
                        state.send_calculation_confirm()
                        confirm_msg = {
                            "message_type": "CALCULATION_CONFIRMATION",
                            "remaining_health": remaining_health,
                            "sequence_number": state.next_sequence_number()
                        }
                        socket_obj.sendto(parser.encode_message(confirm_msg), addr)

                        # Check if both confirmed
                        confirmed_calcu = state.both_confirmed()

                        if confirmed_calcu:
                            pass  # proceed to next turn (both_confirmed switches turn)
                        else:
                            print("Players calculations not yet confirmed.\n")
                            resolution_request = {
                                "message_type": "RESOLUTION_REQUEST",
                                "attacker": pokemon,
                                "move_used": last_attack,
                                "damage_dealt": damage,
                                "defender_hp_remaining": defender_hp_after,
                                "sequence_number": state.next_sequence_number()
                            }
                            
                            socket_obj.sendto(parser.encode_message(resolution_request), addr)

                # Turn switched by both_confirmed(); just print status
                print(status_message)
                print(divider)

    # Game over handling
    game_over = {
        "message_type": "GAME_OVER",
        "winner": state.winner,
        "loser": state.loser,
        "sequence_number": state.next_sequence_number()
    }
    socket_obj.sendto(parser.encode_message(game_over), addr)
    print(f"Congratulations, {state.winner}! You've won!")
    print("=============== GAME OVER! =================")



# Initialize host + game loops
def init():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # set a timeout so recvfrom doesn't block forever
        s.settimeout(20)
        s.bind((HOST, PORT))
        


        
        #! HANDSHAKE INITIATION

        print(divider)
        print(f"[HOST] Host listening on {HOST}:{PORT}...")
        print(f"[HOST] Awaiting handshake...\n")

        # Receives data from client until termination via empty bytes object b''
        while True:
            try:
                data, addr = s.recvfrom(1024)
            except socket.timeout:
                # continue waiting for a handshake; print a notice and keep listening
                print("[HOST] Still waiting for handshake...")
                continue

            client_msg = parser.decode_message(data)

            message_type = client_msg.get("message_type")

            

            #! HANDSHAKE RESPONSE
            
            if message_type == "HANDSHAKE_REQUEST" or message_type == "SPECTATOR_REQUEST":
                if message_type == "HANDSHAKE_REQUEST":
                    role = "Joiner"
                else:
                    role = "Spectator"

                # Handshake response + seed generation
                print(f"[HOST] {role} handshake request received from {addr}\n")

                seed = random.randint(0, 9999)
                host_response = {
                    "message_type": "HANDSHAKE_RESPONSE",
                    "seed": seed
                }
                s.sendto(parser.encode_message(host_response), addr)

                print(f"[HOST] seed generated: {seed}")
                print(f"[HOST] Handshake with {role} complete!\n")

                

                #! BATTLE SETUP INITIATION

                if message_type == "HANDSHAKE_REQUEST":
                    print(top_divider)
                    
                    # Battle setup initiation
                    print(f"Initializing battle setup...\n")

                    # Sending host battle setup data
                    my_poke_data = init_battle()
                    host_response = {
                        "message_type": "BATTLE_SETUP",
                        "battle_data": my_poke_data
                    }
                    s.sendto(parser.encode_message(host_response), addr)

                    # Receiving joiner battle setup data
                    try:
                        data, addr = s.recvfrom(1024)
                    except socket.timeout:
                        print("[HOST] Timeout waiting for BATTLE_SETUP from Joiner. Ending.")
                        break

                    joiner_msg = parser.decode_message(data)
                    print(f"\nBattle setup data received from Joiner:\n{joiner_msg}")
                    print(divider)
                    joiner_data = joiner_msg["battle_data"]



                    #! BATTLE TURN IMPLEMENTATION

                    if joiner_msg["message_type"] == "BATTLE_SETUP":
                        print(f"Battle setup complete! Beginning battle...\n")
                        battle_state = BattleState(
                            is_host=True,
                            seed=seed,
                            verbose=True
                        )
                        
                        # pokemon data shld be imported here (csv)
                        # only battle init data for now
                        battle_state.set_pokemon_data(my_poke_data, joiner_data)

                        start_battle(s, addr, battle_state)

            else:
                print(f"[HOST] Unexpected message type: {message_type}")
                break



# MAIN

init()