# imports
from enum import Enum

"""
manage battle state, turn order, and phase transitions

#! NOT IMPLEMENTED HERE THATS IN SECTION 5:
5.1 Reliability Layer
5.2.3 Discrepancy Resolution
5.2.4 Chat Functionality

ATTACK_ANNOUNCE -> allow sending only if it's the attacker's turn and phase is WAITING_FOR_MOVE
DEFENSE_ANNOUNCE -> move to CALCULATION phase after receiving this
CALCULATION_REPORT -> wait for both sides' reports, update HP, check for win
CALCULATION_CONFIRM -> Once both sides confirm, move to next turn
GAME_OVER -> if HP <= 0, create and send this message
"""

# GLOBAL VARIABLES AND CONSTANTS
class GamePhase(Enum):
    WAITING_FOR_MOVE = "WAITING_FOR_MOVE"
    PROCESSING_TURN = "PROCESSING_TURN"
    GAME_OVER = "GAME_OVER"


# CLASSES
class BattleState:
    def __init__(self, is_host, seed):
        #status
        self.is_host = is_host # boolean true/false
        self.seed = seed
        self.current_phase = GamePhase.WAITING_FOR_MOVE #after BATTLE_SETUP, transition to this
        self.my_turn = is_host # host peer first
        self.sequence_number = 0

        #pokemon stats
        self.my_pokemon = None 
        self.opponent_pokemon = None

        #game state
        self.last_attack = None                     # attack data received
        self.local_calculation = None               # 'hp': int, 'sequence': int
        self.opponent_calculation = None            # opponent's report ^
        self.local_confirm_sent = False             # did we confirm?
        self.opponent_confirm_received = False      # did opponent confirm?
        self.winner = None                          # "me" or "opponent" or None



    #! SETUP

    #pokemon stats
    #call this after BATTLE_SETUP exchange is sent
    def set_pokemon_data(self, my_pokemon: dict, opponent_pokemon: dict):
        self.my_pokemon = my_pokemon
        self.opponent_pokemon = opponent_pokemon
    
    #generate next sequence number
    def next_sequence_number(self) -> int:
        self.sequence_number += 1
        return self.sequence_number
    

    
    #! WAITING_FOR_MOVE

    #check if attacking is allowed
    def can_attack(self) -> bool:
        return self.my_turn and self.current_phase == GamePhase.WAITING_FOR_MOVE
    
    #check if defending is allowed
    def can_defend(self) -> bool:
        return (not self.my_turn) and self.current_phase == GamePhase.WAITING_FOR_MOVE
    
    #check whether to accept the attack
    def receive_attack_announce(self, attack_data) -> bool:
        if self.can_defend():
            self.last_attack = attack_data #store attack data for calculation
            return True #attack was received
        return False #attack not accepted
    
    #transition to PROCESSING_TURN after doing defense (both players)
    def receive_defense_announce(self):
        if self.current_phase == GamePhase.WAITING_FOR_MOVE:
            self.current_phase = GamePhase.PROCESSING_TURN



    #! PROCESSING_TURN

    #store local result of own pokemon hp after damage
    def record_local_calculation(self, my_remaining_hp: int):
        self.local_calculation = {
            'hp': my_remaining_hp,
            'sequence': self.sequence_number # or change if separate tracking is needed
        }

        if self.my_pokemon is not None:
            self.my_pokemon['hp'] = my_remaining_hp #update in view

        self.check_game_over() #check if its over

    #store result if opponent hp
    def receive_calculation_report(self, opponent_hp: int, opponent_seq: int):
        self.opponent_calculation = { #store opponent's calculation report
            'hp' : opponent_hp,
            'sequence' : opponent_seq
        }

        if self.opponent_pokemon is not None:
            self.opponent_pokemon['hp'] = opponent_hp #update in view

        self.check_game_over() #check if its over

    #check if calculation is confirmed
    def send_calculation_confirm(self):
        self.local_confirm_sent = True 

    def receive_calculation_confirm(self):
        self.opponent_confirm_received = True

    #check if both players confirmed calculations, if true, switch turns
    def both_confirmed(self) -> bool:
        if self.is_game_over():
            return True # already game over so no need to switch
        if self.local_confirm_sent and self.opponent_confirm_received:
            self.switch_turn()
            return True
        return False

    def switch_turn(self):
        # clear status every turn
        self.my_turn = not self.my_turn
        self.current_phase = GamePhase.WAITING_FOR_MOVE
        self.last_attack = None
        self.local_calculation = None
        self.opponent_calculation = None
        self.local_confirm_sent = False
        self.opponent_confirm_received = False
        
        # after switching, check if battle ended
        self.check_game_over()



    #! GAME_OVER

    #check if game should end
    def check_game_over(self) -> bool:
        if self.my_pokemon and self.my_pokemon.get('hp', 1) <= 0:
            self.current_phase = GamePhase.GAME_OVER
            self.winner = "opponent"
            return True
        if self.opponent_pokemon and self.opponent_pokemon.get('hp', 1) <= 0:
            self.current_phase = GamePhase.GAME_OVER
            self.winner = "me"
            return True
        return False
    
    #check if game is over
    def is_game_over(self) -> bool:
        return self.current_phase == GamePhase.GAME_OVER