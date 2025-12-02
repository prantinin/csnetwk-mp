from networking.message_parser import MessageParser
from game.battle_state import BattleState
import socket
import random
import ast

parser = MessageParser()

divider = "========================================\n"
your_turn_divider = "================== YOUR TURN ==============\n"
their_turn_divider = "================== OPPONENT'S TURN =======\n"


class Protocols:



    #! INITIALIZATION

    # Host battle setup
    def host_battle_setup(self):
        
        # dummy data
        health = 100
        
        valid_com = False
        valid_poke = False
        
        while not valid_com:
            comms = input("What communication mode would you like? (P2P/BROADCAST) ")
            comms = comms.upper()
            if comms == "P2P" or comms == "BROADCAST":
                valid_com = True
            else:
                print(f"Please choose only between the two avail. modes:>") 
        
        while not valid_poke:
            poke_name = input("Choose your Pokemon: ")

            # change this later. dummy data for now
            poke_data = {
                "pokemon": poke_name,
                "hp": int(health)
            }

            valid_poke = True

        s_atk = input("How much special attack boost? ")
        s_def = input("How much special defense boost? ")

        return {
            "communication_mode": comms,
            "pokemon_name": poke_data,
            "stat_boosts": {
                "special_attack_uses": s_atk,
                "special_defense_uses": s_def
            }
        }
    

    # Joiner battle setup
    def joiner_battle_setup(self):

        # dummy data
        health = 100

        valid_poke = False

        while not valid_poke:
            poke_name = input("Choose your Pokemon: ")

            # change this later. dummy data for now
            poke_data = {
                "pokemon": poke_name,
                "hp": int(health)
            }

            valid_poke = True

        s_atk = input("How much special attack boost? ")
        s_def = input("How much special defense boost? ")

        return {
            "pokemon_name": poke_data,
            "stat_boosts": {
                "special_attack_uses": s_atk,
                "special_defense_uses": s_def
            }
        }
    






    #! GAME TURNS

    @staticmethod
    def calculate_damage(health, damage):
        return health - damage

    def your_turn(self, socket_obj, addr, state: BattleState):
        #! WAITING_FOR_MOVE

        # You choosing attack move
        # pls remember to lower() pokemon moves from cv as well
        print(your_turn_divider)
        move_name = input("Choose your attack move: ").lower()
        my_move = {
            "message_type": "ATTACK_ANNOUNCE",
            "move_name": {          # will fix later when data is properly parsed
                "move": move_name,
                "move_damage": 20
            },
            "sequence_number": state.next_sequence_number()
        }
        state.record_attack_announce(my_move['move_name'])
        socket_obj.sendto(parser.encode_message(my_move).encode(), addr)

        # Awaiting opp def announcement
        print("\nAttack announcement sent. Awaiting defense announcement...")

        data, __ = socket_obj.recvfrom(1024)
        recvd_msg = parser.decode_message(data.decode())

        if recvd_msg['message_type'] == "DEFENSE_ANNOUNCE":
            state.receive_defense_announce()
            print("Opponent defense announcement received. Beginning damage calculation...\n")
            print(state.check_battle_state())


            confirmed_calcu = False
            while not confirmed_calcu:

                #! PROCESSING_TURN
                # Preparing calculation report
                remaining_health = Protocols.calculate_damage(state.opponent_pokemon['hp'], state.last_attack['move_damage'])
                state.record_local_calculation(remaining_health)

                # Status message following calculation confirmation
                effect = "super effective"  # example palang
                status_message = (f"{state.my_pokemon['pokemon']} used {state.last_attack['move']}! It was {effect}!")

                # Converting strings to dict
                

                # Send calculation report
                calcu_report = {
                    "message_type": "CALCULATION_REPORT",
                    "attacker": state.my_pokemon['pokemon'],
                    "move_used": my_move['move_name']['move'],      # will change later
                    "remaining_health": state.my_pokemon['hp'],
                    "damage_dealt": my_move['move_name']['move_damage'],    # will change later
                    "defender_hp_remaining": state.opponent_pokemon['hp'],
                    "status_message": status_message,
                    "sequence_number": state.next_sequence_number()
                }
                socket_obj.sendto(parser.encode_message(calcu_report).encode(), addr)
                print("Calculation report sent! Checking for discrepancies...\n")

                # Awaiting opp calculation confirmation
                data, __ = socket_obj.recvfrom(1024)
                recvd_msg = parser.decode_message(data.decode())
                print('\n')
                battle_state_checker = state.check_battle_state()
                print(battle_state_checker)

                if recvd_msg['message_type'] == "CALCULATION_CONFIRMATION":
                    #state.receive_calculation_report(
                    #        recvd_msg.get("remaining_health"),
                    #        recvd_msg.get("sequence_number")
                    #    )
                    print("All calculations similar! Turn end!")
                    state.switch_turn()
                    confirmed_calcu = True

                
                # if resolution req, repeat calcu
                else:
                    print(f"Received message type {recvd_msg}. Recomputing damage...")

                    # remove in case of infinite loop
                    break

    def their_turn(self, socket_obj, addr, state: BattleState):
        #! WAITING_FOR_MOVE

        # Awaiting opp attack announce
        print(their_turn_divider)
        print("Waiting for opponent's move...\n")

        data, __ = socket_obj.recvfrom(1024)
        recvd_msg = parser.decode_message(data.decode())

        accepted = state.receive_attack_announce(recvd_msg['move_name'])

        if accepted:
            print(f"Opponent attack received: {accepted}")

            # Sending def announcement
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
                state.receive_calculation_confirm()
                state.receive_calculation_report(
                    int(recvd_msg['defender_hp_remaining']), 
                    int(recvd_msg['sequence_number'])
                )
                
                print(f"Received opponent calculation report:\n {recvd_msg}\n")
                print("Beginning own damage calculation...")


                # Preparing own calculation report
                if isinstance(state.my_pokemon, str):
                    state.my_pokemon = ast.literal_eval(state.my_pokemon)

                if isinstance(state.opponent_pokemon, str):
                    state.opponent_pokemon = ast.literal_eval(state.opponent_pokemon)

                if isinstance(state.last_attack, str):
                    state.last_attack = ast.literal_eval(state.last_attack)

                remaining_health = Protocols.calculate_damage(state.my_pokemon['hp'], state.last_attack['move_damage'])
                state.record_local_calculation(remaining_health)

                # Status message following calculation confirmation
                effect = "super effective"  # example palang
                status_message = (f"{state.opponent_pokemon['pokemon']}'s {state.last_attack['move']} hit {state.my_pokemon['pokemon']}! It was {effect}!")

                # Send calculation report
                # Convert strings to dicts after receiving
                calcu_report = {
                    "message_type": "CALCULATION_REPORT",
                    "attacker": state.opponent_pokemon['pokemon'],
                    "move_used": state.last_attack['move'],
                    "remaining_health": state.opponent_pokemon['hp'],
                    "damage_dealt": state.last_attack['move_damage'],             
                    "defender_hp_remaining": state.my_pokemon['hp'],
                    "status_message": status_message,
                    "sequence_number": state.next_sequence_number()
                }         
                state.send_calculation_confirm()        # not sure ab tis
                print("Calculation report complete.")
                print("Comparing my and opponent reports...")

                # Comparing calculation reports
                if state.both_confirmed():
                    print(f"Calculation reports similar: {confirmed_calcu}")
                    confirmed_msg = {
                        "message_type": "CALCULATION_CONFIRMATION",
                        "sequence_number": state.next_sequence_number()
                    }
                    socket_obj.sendto(parser.encode_message(confirmed_msg).encode(), addr)
                    confirmed_calcu = True
                else:
                    print(f"Calculation reports similar: {confirmed_calcu}")
                    print("Sending resolution request...")
                    res_req_msg = {
                        "message_type": "RESOLUTION_REQUEST",
                        "attacker": state.opponent_pokemon['pokemon'],
                        "move_used": state.last_attack['move'],
                        "damage_dealt": state.last_attack['move_damage'],
                        "defender_hp_remaining": None,
                        "sequence_number": state.next_sequence_number()
                    }
                    socket_obj.sendto(parser.encode_message(res_req_msg).encode(), addr)

            
        else:
            print(f"Unexpected message received:\n{recvd_msg}")

    # Modified start_game to call the two functions
    def start_game(self, socket_obj, addr, state: BattleState):

        while not state.is_game_over():
            if state.my_turn:
                self.your_turn(socket_obj, addr, state)
            else:
                self.their_turn(socket_obj, addr, state)