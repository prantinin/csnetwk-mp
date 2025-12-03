# imports
from enum import Enum

"""
manage battle state, turn order, and phase transitions

#! NOT IMPLEMENTED HERE THATS IN SECTION 5:
5.1 Reliability Layer
5.2.3 Discrepancy Resolution
5.2.4 Chat Functionality
"""

# GLOBAL VARIABLES AND CONSTANTS
class GamePhase(Enum):
    WAITING_FOR_MOVE = "WAITING_FOR_MOVE"
    PROCESSING_TURN = "PROCESSING_TURN"
    GAME_OVER = "GAME_OVER"


# CLASSES
class BattleState:
    def __init__(self, is_host, seed, verbose=False):
        #status
        self.is_host = is_host # boolean true/false
        self.seed = seed
        self.current_phase = GamePhase.WAITING_FOR_MOVE #after BATTLE_SETUP, transition to this
        self.my_turn = is_host # host peer first
        self.sequence_number = 0
        self.verbose = verbose

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

    #for verbose mode or debugging
    def log(self, *args):
        if self.verbose:
            role = "HOST" if self.is_host else "JOINER"
            print(f"[DBUG:{role}]", *args)

    #pokemon stats
    #call this after BATTLE_SETUP exchange is sent
    def set_pokemon_data(self, my_pokemon: dict, opponent_pokemon: dict):
        self.my_pokemon = my_pokemon
        self.opponent_pokemon = opponent_pokemon
        self.log("Pokemon data set: Mine HP:", my_pokemon.get('hp'), "Opponent HP:", opponent_pokemon.get('hp'))
    
    #generate next sequence number
    def next_sequence_number(self) -> int:
        self.sequence_number += 1
        self.log("Next sequence number:", self.sequence_number)
        return self.sequence_number
    

    
    #! WAITING_FOR_MOVE

    #check if attacking is allowed
    def can_attack(self) -> bool:
        allowed = self.my_turn and self.current_phase == GamePhase.WAITING_FOR_MOVE
        self.log("Can attack:", allowed)
        return allowed
    
    #check if defending is allowed
    def can_defend(self) -> bool:
        allowed = (not self.my_turn) and self.current_phase == GamePhase.WAITING_FOR_MOVE
        self.log("Can defend:", allowed)
        return allowed
    
    #check whether to accept the attack
    def receive_attack_announce(self, attack_data) -> bool:
        if self.can_defend():
            self.last_attack = attack_data #store attack data for calculation
            self.log("Received attack announce:", attack_data)
            return True #attack was received
        self.log("Rejected attack announce (not in correct state)")
        return False #attack not accepted
    
    def record_attack_announce(self, attack_data):
        self.last_attack = attack_data
        self.log("Recorded attack: ", attack_data)
    
    #transition to PROCESSING_TURN after doing defense (both players)
    def receive_defense_announce(self):
        if self.current_phase == GamePhase.WAITING_FOR_MOVE:
            self.log("Received defense announce. Moving to PROCESSING_TURN")
            self.current_phase = GamePhase.PROCESSING_TURN



    #! PROCESSING_TURN

    #store local result of own pokemon hp after damage
    def record_local_calculation(self, my_remaining_hp: int):
        self.local_calculation = {
            'hp': my_remaining_hp,
            'sequence': self.sequence_number # or change if separate tracking is needed
        }

        #if self.my_pokemon is not None:
        #    self.my_pokemon['hp'] = my_remaining_hp #update in view

        self.log("Recorded local calculation. My HP:", my_remaining_hp)
        self.check_game_over() #check if its over

    #store result if opponent hp
    def receive_calculation_report(self, opponent_hp: int, opponent_seq: int):
        self.opponent_calculation = { #store opponent's calculation report
            'hp' : opponent_hp,
            'sequence' : opponent_seq
        }

        #if self.opponent_pokemon is not None:
        #    self.opponent_pokemon['hp'] = opponent_hp #update in view

        self.log("Received opponent calculation. Opponent HP:", opponent_hp)
        self.check_game_over() #check if its over

    #check if calculation is confirmed
    def send_calculation_confirm(self):
        self.local_confirm_sent = True 
        self.log("Sent calculation confirm.")

    def receive_calculation_confirm(self):
        self.opponent_confirm_received = True
        self.log("Received opponent calculation confirm.")

    #check if both players confirmed calculations, if true, switch turns
    def both_confirmed(self) -> bool:
        if self.is_game_over():
            return True # already game over so no need to switch
        if self.local_confirm_sent and self.opponent_confirm_received:
            self.log("Both players confirmed calculations. Switching turn.")
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

        # Switch pokemon possession
        temp = self.my_pokemon
        self.my_pokemon = self.opponent_pokemon
        self.opponent_pokemon = temp
        
        self.log("Switched turn. My turn:", self.my_turn)
        # after switching, check if battle ended
        self.check_game_over()



    #! GAME_OVER

    #check if game should end
    def check_game_over(self) -> bool:
        if self.my_pokemon and self.my_pokemon.get('hp', 1) <= 0:
            self.current_phase = GamePhase.GAME_OVER
            self.winner = "opponent"
            self.log("Game over. Winner: opponent")
            return True
        if self.opponent_pokemon and self.opponent_pokemon.get('hp', 1) <= 0:
            self.current_phase = GamePhase.GAME_OVER
            self.winner = "me"
            self.log("Game over. Winner: me")
            return True
        return False
    
    #check if game is over
    def is_game_over(self) -> bool:
        over = self.current_phase == GamePhase.GAME_OVER
        if over:
            self.log("Game is over.")
        return over



    # --- DISCREPANCY HANDLING HELPERS ---

    def check_battle_state(self) -> dict:
        return {
            "is_host": self.is_host,
            "seed": self.seed,
            "current_phase": self.current_phase.name,
            "my_turn": self.my_turn,
            "sequence_number": self.sequence_number,
            "last_attack": self.last_attack,
            "local_calculation": self.local_calculation,
            "opponent_calculation": self.opponent_calculation,
            "local_confirm_sent": self.local_confirm_sent,
            "opponent_confirm_received": self.opponent_confirm_received,
            "winner": self.winner,
            "my_pokemon": str(self.my_pokemon) if self.my_pokemon else None,
            "opponent_pokemon": str(self.opponent_pokemon) if self.opponent_pokemon else None,
        }
    
    def check_my_opp_pokemon(self) -> dict:
        return {
            "local_calculation": self.local_calculation,
            "opponent_calculation": self.opponent_calculation,
            "my_pokemon": str(self.my_pokemon) if self.my_pokemon else None,
            "opponent_pokemon": str(self.opponent_pokemon) if self.opponent_pokemon else None,
        }

    def has_discrepancy(self) -> bool:
        """
        Returns True if we have both local_calculation and opponent_calculation
        and they do NOT match (HP or sequence).
        """
        if self.local_calculation is None or self.opponent_calculation is None:
            self.log("No full calculations yet; cannot check discrepancy.")
            return False

        same_seq = self.local_calculation.get("sequence") == self.opponent_calculation.get("sequence")
        same_hp = self.local_calculation.get("hp") == self.opponent_calculation.get("hp")

        self.log(
            "Checking discrepancy:",
            f"local_hp={self.local_calculation.get('hp')}",
            f"opponent_hp={self.opponent_calculation.get('hp')}",
            f"same_seq={same_seq}",
            f"same_hp={same_hp}",
        )

        return not (same_seq and same_hp)

    def get_resolution_payload(self) -> dict:
        """
        Build the minimal information needed to send in a RESOLUTION_REQUEST
        based on our local calculation.
        """
        if self.local_calculation is None:
            self.log("No local calculation; cannot build resolution payload.")
            return {}

        return {
            "remaining_health": self.local_calculation.get("hp"),
            "sequence_number": self.local_calculation.get("sequence"),
        }

    def apply_resolved_opponent_hp(self, resolved_hp: int):
        """
        Called when the peers agree on a final HP for the defender after
        discrepancy resolution.
        """
        if self.opponent_pokemon is not None:
            self.opponent_pokemon["hp"] = resolved_hp

        if self.opponent_calculation is None:
            self.opponent_calculation = {}

        self.opponent_calculation["hp"] = resolved_hp
        self.log("Applied resolved opponent HP:", resolved_hp)
        self.check_game_over()
	
    def force_terminate_due_to_mismatch(self):
        """
        Terminate the battle because damage calculations could not be reconciled
        after a RESOLUTION_REQUEST / re-evaluation.
        """
        self.current_phase = GamePhase.GAME_OVER
        # we don't assign a winner here because the result is ambiguous
        self.winner = None
        self.log("Battle terminated due to unresolved damage discrepancy.")

