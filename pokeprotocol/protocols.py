from networking.message_parser import MessageParser
from game.battle_state import BattleState
from game.pokemon_stats import load_pokemon_stats, get_by_name, pokemon_to_dict
from game.damage_calculator import calculate_damage


import socket

parser = MessageParser()

divider = "========================================\n"
your_turn_divider = "================== YOUR TURN ==============\n"
their_turn_divider = "================== OPPONENT'S TURN =======\n"


class Protocols:

    def __init__(self):
        self.pokemon_stats = load_pokemon_stats("game/pokemon.csv")
        print("Pokemon stats loaded!")



    #! INITIALIZATION

    # Host battle setup
    def host_battle_setup(self):
        
        valid_com = False
        valid_poke = False
        valid_atk = False
        valid_def = False
        
        while not valid_com:
            comms = input("What communication mode would you like? (P2P/BROADCAST) ")
            comms = comms.upper()
            if comms == "P2P" or comms == "BROADCAST":
                valid_com = True
            else:
                print(f"Please choose only between the two avail. modes:>") 
        
        while not valid_poke:
            poke_name = input("Choose your Pokemon: ").capitalize()

            pokemon = get_by_name(poke_name, self.pokemon_stats)

            if pokemon is None:
                print("Pokemon not found in CSV. Try again.")
                continue
            
            #DEBUG
            print(pokemon)

            valid_poke = True

        while not valid_atk:
            s_atk = input("How much special attack boost? ").strip()

            if not s_atk.isdigit():
                print("Enter digits only.")
                continue

            valid_atk = True

        while not valid_def:
            s_def = input("How much special defense boost? ")

            if not s_def.isdigit():
                print("Enter digits only.")
                continue

            valid_def = True

        poke_stats = {
            "communication_mode": comms,
            "pokemon_name": pokemon.name,
            "stat_boosts": {
                "special_attack_uses": int(s_atk),
                "special_defense_uses": int(s_def)
            },
            "pokemon": pokemon_to_dict(pokemon)
        }

        #DEBUG
        print(poke_stats)

        return poke_stats
    

    # Joiner battle setup
    def joiner_battle_setup(self):
        
        valid_poke = False
        valid_atk = False
        valid_def = False
        
        while not valid_poke:
            poke_name = input("Choose your Pokemon: ").capitalize()

            pokemon = get_by_name(poke_name, self.pokemon_stats)

            if pokemon is None:
                print("Pokemon not found in CSV. Try again.")
                continue
            
            #DEBUG
            print(pokemon)

            valid_poke = True

        while not valid_atk:
            s_atk = input("How much special attack boost? ").strip()

            if not s_atk.isdigit():
                print("Enter digits only.")
                continue

            valid_atk = True

        while not valid_def:
            s_def = input("How much special defense boost? ")

            if not s_def.isdigit():
                print("Enter digits only.")
                continue

            valid_def = True

        poke_stats = {
            "pokemon_name": pokemon.name,
            "stat_boosts": {
                "special_attack_uses": int(s_atk),
                "special_defense_uses": int(s_def)
            },
            "pokemon": pokemon_to_dict(pokemon)
        }

        #DEBUG
        print(poke_stats)

        return poke_stats
    






    #! GAME TURNS

    @staticmethod
    def subtract_damage(health, damage):
        return health - damage

    # PLAYER ATTACKS, OPPONENT DEFENDS
    def your_turn(self, socket_obj, addr, state: BattleState):
        
        
        #! WAITING_FOR_MOVE

        # Choosing attack move
        print(your_turn_divider)
        move_name = input("Choose your attack move: ").capitalize()
        
        # Deciding on stat boost
        if int(state.stat_boosts['special_attack_uses']) > 0 or int(state.stat_boosts['special_defense_uses']) > 0:
            print("Stat boosts:")
            print(f"Attack boosts left: {state.stat_boosts['special_attack_uses']}")
            print(f"Defense boosts left: {state.stat_boosts['special_defense_uses']}")
            
            valid_stat = False
            while not valid_stat:
                use_stat = input("Would you like to use a special stat boost? (y/n)")

                if use_stat != "y" and use_stat != "n":
                    print("Answer with y/n only.")
                    continue
                    
                valid_stat = True
            
            valid_stat = False
            if use_stat == "y":
                while not valid_stat:
                    # This will be used in damage calculation later
                    decide_stat_boost = input("Use special attack/defense boost? (atk/def)")

                    if decide_stat_boost != "atk" and decide_stat_boost != "def":
                        print("Answer with atk/def only.")
                        continue
                    if decide_stat_boost == "atk" and int(state.stat_boosts['special_attack_uses']) == 0:
                        print("You're out of special attack boosts!")
                        continue
                    if decide_stat_boost == "def" and int(state.stat_boosts['special_defense_uses']) == 0:
                        print("You're out of special defense boosts!")
                        continue
                    
                    valid_stat = True
            else:
                decide_stat_boost = "none"
        
        # Sending my move to opponent
        my_move = {
            "message_type": "ATTACK_ANNOUNCE",
            "move_name": move_name,
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

                damage = calculate_damage(state, decide_stat_boost, your_turn=True)
                remaining_health = Protocols.subtract_damage(state.opponent_pokemon['hp'], damage)
                
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
                status_message = (f"{state.my_pokemon['name']} used {state.last_attack}! It was {effect}!")

                # Send calculation report
                calcu_report = {
                    "message_type": "CALCULATION_REPORT",
                    "attacker": state.my_pokemon['name'],
                    "move_used": my_move['move_name'],
                    "remaining_health": state.my_pokemon['hp'],
                    "damage_dealt": damage,    # will change later
                    "defender_hp_remaining": remaining_health,
                    "status_message": status_message,
                    "decide_stat_boost": decide_stat_boost,
                    "sequence_number": state.next_sequence_number()
                }
                
                #DEBUG
                print(f"Check other: {state.my_pokemon['hp']}")
                
                socket_obj.sendto(parser.encode_message(calcu_report).encode(), addr)
                state.send_calculation_confirm()
                state.record_local_calculation(remaining_health)
                print("Calculation report sent! Waiting for opponent report...\n")

                #DEBUG
                print(f"Check other: {state.my_pokemon['hp']}")

                # Receive opp calculation report
                data, __ = socket_obj.recvfrom(1024)
                recvd_msg = parser.decode_message(data.decode())
                state.receive_calculation_confirm()
                state.receive_calculation_report(
                    int(recvd_msg['defender_hp_remaining']), 
                    int(recvd_msg['sequence_number'])
                )
                print(f"Check other: {state.my_pokemon['hp']}")
                print("Opponent report received! Comparing reports...")
                print(recvd_msg)
                print('\n')

                # Comparing reports
                if recvd_msg['message_type'] == "CALCULATION_REPORT":
                    
                    #DEBUG
                    print(state.check_battle_state())

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
                        
                        # Update stat boost used
                        if decide_stat_boost != "none":
                            state.decrease_stat_boost(decide_stat_boost)

                        # Printing status messages
                        print(status_message)
                        print(f"{state.opponent_pokemon['name']}: -{damage} hp")

                        # Switch turns and exit loop
                        state.switch_turn()
                        confirmed_calcu = True

                        #DEBUG
                        print(state.check_battle_state())



                        #! GAME_OVER
                        # Receiving/sending any game over messages
                        if state.winner == "me":
                            game_over = {
                                "message_type": "GAME_OVER",
                                "winner": state.my_pokemon['name'],
                                "loser": state.opponent_pokemon['name'], 
                                "sequence_number": state.next_sequence_number()
                            }
                            socket_obj.sendto(parser.encode_message(game_over).encode(), addr)
                            print(f"{state.opponent_pokemon['name']} has fainted! You win, {state.my_pokemon['name']}!")
                        elif state.winner == "opponent":
                            data, __ = socket_obj.recvfrom(1024)
                            recvd_msg = parser.decode_message(data.decode())
                            print(f"{state.my_pokemon['name']} has fainted! You win, {state.opponent_pokemon['name']}!")

                            
                    else:
                        print(f"Received {recvd_msg['message_type']}!")
                        print("Recalculating...")

                # Dissimilar turns, recalculate
                else:
                    print(f"Calculation reports similar: {confirmed_calcu}")
                    print("Sending resolution request...")
                    res_req_msg = {
                        "message_type": "RESOLUTION_REQUEST",
                        "attacker": state.my_pokemon['name'],
                        "move_used": state.last_attack,
                        "damage_dealt": damage,
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

                #DEBUG
                print(f"before calcu: {state.my_pokemon['hp']}")
                
                damage = calculate_damage(state, recvd_msg['decide_stat_boost'], your_turn=False)
                remaining_health = Protocols.subtract_damage(state.my_pokemon['hp'], damage)
                
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
                status_message = (f"{state.my_pokemon['name']}'s {state.last_attack} hit {state.opponent_pokemon['name']}! It was {effect}!")

                # Send calculation report
                calcu_report = {
                    "message_type": "CALCULATION_REPORT",
                    "attacker": state.opponent_pokemon['name'],
                    "move_used": state.last_attack,
                    "remaining_health": state.opponent_pokemon['hp'],
                    "damage_dealt": damage,             
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
                    
                    #DEBUG
                    print(state.check_battle_state())

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
                        print(f"{state.my_pokemon['name']}: -{damage} hp")

                        # Switch turns and exit loop
                        state.switch_turn()
                        confirmed_calcu = True



                        #! GAME_OVER
                        # Receiving/sending any game over messages
                        if state.winner == "me":
                            game_over = {
                                "message_type": "GAME_OVER",
                                "winner": state.my_pokemon['name'],
                                "loser": state.opponent_pokemon['name'], 
                                "sequence_number": state.next_sequence_number()
                            }
                            socket_obj.sendto(parser.encode_message(game_over).encode(), addr)
                            print(f"{state.opponent_pokemon['name']} has fainted! You win, {state.my_pokemon['name']}!")
                        elif state.winner == "opponent":
                            data, __ = socket_obj.recvfrom(1024)
                            recvd_msg = parser.decode_message(data.decode())
                            print(f"{state.my_pokemon['name']} has fainted! You win, {state.opponent_pokemon['name']}!")

                    # I say reports are not similar
                    else:
                        print(f"Calculation reports similar: {confirmed_calcu}")
                        print("Sending resolution request...")
                        res_req_msg = {
                            "message_type": "RESOLUTION_REQUEST",
                            "attacker": state.my_pokemon['name'],
                            "move_used": state.last_attack,
                            "damage_dealt": damage,
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