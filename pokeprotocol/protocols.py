from networking.message_parser import MessageParser
from game.battle_state import BattleState
from game.pokemon_stats import load_pokemon_stats, get_by_name
from game.damage_calculator import calculate_damage


import socket

parser = MessageParser()

divider = "========================================\n"
your_turn_divider = "================== YOUR TURN ==============\n"
their_turn_divider = "================== OPPONENT'S TURN =======\n"


class Protocols:

    def __init__(self):
        self.pokemon_stats = load_pokemon_stats("game/pokemon.csv")

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

            pokemon = get_by_name(poke_name, self.pokemon_stats)

            if pokemon is None:
                print("Pokemon not found in CSV. Try again.")
                continue

            poke_data = self.pokemon_to_dict(pokemon)
            
            #DEBUG
            print(poke_data)

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
        health = 140

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

    # PLAYER ATTACKS, OPPONENT DEFENDS
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
        print("\nAttack announcement sent. Awaiting defense announcement...")

         # Awaiting opp def announcement
        data, __ = socket_obj.recvfrom(1024)
        recvd_msg = parser.decode_message(data.decode())

        if recvd_msg['message_type'] == "DEFENSE_ANNOUNCE":
            state.receive_defense_announce()
            print("Opponent defense announcement received. Beginning damage calculation...\n")
            
            #DEBUG
            print(state.check_battle_state())
            print('\n')

            confirmed_calcu = False
            while not confirmed_calcu:
                
                
                
                #! PROCESSING_TURN
                # Preparing calculation report
                
                #DEBUG
                print(f"before calcu: {state.opponent_pokemon['hp']}")

                remaining_health = Protocols.calculate_damage(state.opponent_pokemon['hp'], state.last_attack['move_damage'])
                
                #DEBUG
                print(f"After calculation: {remaining_health}")

                state.opponent_pokemon['hp'] = remaining_health
                
                #DEBUG
                print(f"changed hp: {state.opponent_pokemon}")
                print(f"After recording: {state.opponent_pokemon['hp']}")
                print(f"Check other: {state.my_pokemon['hp']}")
                
                #DEBUG
                print(state.check_battle_state())
                print('\n')

                # Status message following calculation confirmation
                effect = "super effective"  # example palang
                status_message = (f"{state.my_pokemon['pokemon']} used {state.last_attack['move']}! It was {effect}!")

                # Send calculation report
                calcu_report = {
                    "message_type": "CALCULATION_REPORT",
                    "attacker": state.my_pokemon['pokemon'],
                    "move_used": my_move['move_name']['move'],      # will change later
                    "remaining_health": state.my_pokemon['hp'],
                    "damage_dealt": my_move['move_name']['move_damage'],    # will change later
                    "defender_hp_remaining": remaining_health,
                    "status_message": status_message,
                    "sequence_number": state.next_sequence_number()
                }
                
                #DEBUG
                print(f"Check other: {state.my_pokemon['hp']}")
                
                state.send_calculation_confirm()
                socket_obj.sendto(parser.encode_message(calcu_report).encode(), addr)
                print("Calculation report sent! Waiting for opponent report...\n")

                #DEBUG
                print(f"Check other: {state.my_pokemon['hp']}")

                # Receive opp calculation report
                data, __ = socket_obj.recvfrom(1024)
                recvd_msg = parser.decode_message(data.decode())
                state.receive_calculation_confirm()
                print(f"Check other: {state.my_pokemon['hp']}")
                print("Opponent report received! Comparing reports...")
                print(recvd_msg)
                print('\n')

                # Comparing reports
                if recvd_msg['message_type'] == "CALCULATION_REPORT":
                    
                    # Similar reports -> switch turns
                    if state.both_confirmed():
                        print(f"Calculation reports similar!")

                    #DEBUG
                    print(state.check_my_opp_pokemon())
                        
                    confirmed_msg = {
                        "message_type": "CALCULATION_CONFIRMATION",
                        "sequence_number": state.next_sequence_number()
                    }
                    socket_obj.sendto(parser.encode_message(confirmed_msg).encode(), addr)
                    confirmed_calcu = True

                    # Check if opponent has same calcu
                    data, __ = socket_obj.recvfrom(1024)
                    recvd_msg = parser.decode_message(data.decode())

                    if recvd_msg['message_type'] == "CALCULATION_CONFIRMATION":
                        print("Opponent has same calcu!")

                        # Printing status messages
                        print(status_message)
                        print(f"{state.opponent_pokemon['pokemon']}: -{state.last_attack['move_damage']} hp")

                        state.switch_turn()

                        #DEBUG
                        print(state.check_battle_state())



                        #! GAME_OVER
                        # Receiving/sending any game over messages
                        if state.winner == "me":
                            game_over = {
                                "message_type": "GAME_OVER",
                                "winner": state.my_pokemon['pokemon'],
                                "loser": state.opponent_pokemon['pokemon'], 
                                "sequence_number": state.next_sequence_number()
                            }
                            socket_obj.sendto(parser.encode_message(game_over).encode(), addr)
                            print(f"{state.opponent_pokemon['pokemon']} has fainted! You win, {state.my_pokemon['pokemon']}!")
                        elif state.winner == "opponent":
                            data, __ = socket_obj.recvfrom(1024)
                            recvd_msg = parser.decode_message(data.decode())
                            print(f"{state.my_pokemon['pokemon']} has fainted! You win, {state.opponent_pokemon['pokemon']}!")

                            
                    else:
                        print(f"Received {recvd_msg['message_type']}!")
                        print("Recalculating...")

                # Dissimilar turns, recalculate
                else:
                    print(f"Calculation reports similar: {confirmed_calcu}")
                    print("Sending resolution request...")
                    res_req_msg = {
                        "message_type": "RESOLUTION_REQUEST",
                        "attacker": state.my_pokemon['pokemon'],
                        "move_used": state.last_attack['move'],
                        "damage_dealt": state.last_attack['move_damage'],
                        "defender_hp_remaining": state.opponent_pokemon['hp'],
                        "sequence_number": state.next_sequence_number()
                    }
                    socket_obj.sendto(parser.encode_message(res_req_msg).encode(), addr)

        
        # if resolution req, repeat calcu
        else:
            print(f"Received message type {recvd_msg}. Recomputing damage...")



    # PLAYER DEFENDS, OPPONENT ATTACKS
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

                #DEBUG
                print(state.check_battle_state())

                print("Beginning own damage calculation...")

                # Preparing own calculation report
                attacker = recvd_msg['attacker']
                
                #DEBUG
                print(f"before calcu: {state.my_pokemon['hp']}")
                
                remaining_health = Protocols.calculate_damage(state.my_pokemon['hp'], state.last_attack['move_damage'])
                
                #DEBUG
                print(f"after calcu: {remaining_health}")

                state.my_pokemon['hp'] = remaining_health

                #DEBUG
                print(f"changed hp: {state.my_pokemon}")
                print(f"After recording: {state.my_pokemon['hp']}")
                print(f"Check other: {state.opponent_pokemon['hp']}")
                
                #DEBUG
                print(state.check_battle_state())
                print('\n')

                # Status message following calculation confirmation
                effect = "super effective"  # example palang
                status_message = (f"{state.my_pokemon['pokemon']}'s {state.last_attack['move']} hit {state.opponent_pokemon['pokemon']}! It was {effect}!")

                # Send calculation report
                calcu_report = {
                    "message_type": "CALCULATION_REPORT",
                    "attacker": state.opponent_pokemon['pokemon'],
                    "move_used": state.last_attack['move'],
                    "remaining_health": state.opponent_pokemon['hp'],
                    "damage_dealt": state.last_attack['move_damage'],             
                    "defender_hp_remaining": remaining_health,
                    "status_message": status_message,
                    "sequence_number": state.next_sequence_number()
                }         
                socket_obj.sendto(parser.encode_message(calcu_report).encode(), addr)
                state.send_calculation_confirm()
                state.record_local_calculation(remaining_health)
                
                print("Calculation report complete and sent to opponent.")
                print("Awaiting opponent results...")

                #DEBUG
                print(state.check_battle_state())
                print('\n')

                # Receiving opponent message
                data, __ = socket_obj.recvfrom(1024)
                recvd_msg = parser.decode_message(data.decode())

                # Opponent says reports are similar
                if recvd_msg['message_type'] == "CALCULATION_CONFIRMATION":
                    
                    # I say reports are similar
                    if state.both_confirmed():
                        print(f"Calculation reports similar!")

                        #DEBUG
                        print(state.check_battle_state())

                        confirmed_msg = {
                            "message_type": "CALCULATION_CONFIRMATION",
                            "sequence_number": state.next_sequence_number()
                        }
                        socket_obj.sendto(parser.encode_message(confirmed_msg).encode(), addr)

                        # Printing status messages
                        print(status_message)
                        print(f"{state.opponent_pokemon['pokemon']}: -{state.last_attack['move_damage']} hp")

                        state.switch_turn()
                        confirmed_calcu = True



                        #! GAME_OVER
                        # Receiving/sending any game over messages
                        if state.winner == "me":
                            game_over = {
                                "message_type": "GAME_OVER",
                                "winner": state.my_pokemon['pokemon'],
                                "loser": state.opponent_pokemon['pokemon'], 
                                "sequence_number": state.next_sequence_number()
                            }
                            socket_obj.sendto(parser.encode_message(game_over).encode(), addr)
                            print(f"{state.opponent_pokemon['pokemon']} has fainted! You win, {state.my_pokemon['pokemon']}!")
                        elif state.winner == "opponent":
                            data, __ = socket_obj.recvfrom(1024)
                            recvd_msg = parser.decode_message(data.decode())
                            print(f"{state.my_pokemon['pokemon']} has fainted! You win, {state.opponent_pokemon['pokemon']}!")

                    # I say reports are not similar
                    else:
                        print(f"Calculation reports similar: {confirmed_calcu}")
                        print("Sending resolution request...")
                        res_req_msg = {
                            "message_type": "RESOLUTION_REQUEST",
                            "attacker": state.my_pokemon['pokemon'],
                            "move_used": state.last_attack['move'],
                            "damage_dealt": state.last_attack['move_damage'],
                            "defender_hp_remaining": state.opponent_pokemon['hp'],
                            "sequence_number": state.next_sequence_number()
                        }
                        socket_obj.sendto(parser.encode_message(res_req_msg).encode(), addr)
                else:
                    print(f"Calculation reports dissimilar.")
                    print("Sending resolution request...")

        
        else:
            print(f"Unexpected message received:\n{recvd_msg}")



    # Modified start_game to call the two functions
    def start_game(self, socket_obj, addr, state: BattleState):

        while not state.check_game_over():
            if state.my_turn:
                self.your_turn(socket_obj, addr, state)
            else:
                self.their_turn(socket_obj, addr, state)

        # will add gameover things later
        print("\n\n\n ==== Game Over ====\n\n\n")