# damage formulas and win/loss check 
#Added Type Effectiveness

""" Not yet integrated into battle_state.py"""


from game.battle_state import BattleState
from game.pokemon_stats import get_by_name, pokemon_to_dict

#------------------------ Damage Calculation -----------------------------------------------
def calculate_damage(state: BattleState, stat_confirm, your_turn):
    """Calculate damage with debug info."""

    # For easier reference
    if your_turn:
        attacker = state.my_pokemon
        defender = state.opponent_pokemon
    else:
        attacker = state.opponent_pokemon
        defender = state.my_pokemon

    # fixed base power because the csv doesnt have this
    # what does it mean that it has to be editable
    base_power = 20

    # Refer to pokemon's special attack boost
    if stat_confirm == "atk":
        atk_stat = attacker['sp_attack']
        def_stat = defender['defense']

    # Refer to pokemon's special defense boost
    elif stat_confirm == "def":
        atk_stat = attacker['attack']
        def_stat = defender['sp_defense']
    
    # Pokemons' normal stats
    else:
        atk_stat = attacker['attack']
        def_stat = defender['defense']
    
    #DEBUG 
    print(f"[DEBUG] Attacker stat: {atk_stat}\nDefender stat: {def_stat}")

    # Getting attacker's type effectiveness against defender
    type1_eff = get_type_effectiveness(defender, attacker['type1'])

    if attacker['type2'] != None:
        type2_eff = get_type_effectiveness(defender, attacker['type2'])
    else:
        type2_eff = 1.0
    
    #DEBUG
    print(f"[DEBUG] Attacker type1 effectiveness: {type1_eff}\nAttacker type1 effectiveness: {type2_eff}")

    # Actual damage calculation
    damage = (base_power * atk_stat * type1_eff * type2_eff) / max(def_stat, 1)
    variance = state.rng.uniform(0.85, 1.0)
    final_damage = max(1, int(damage * variance))

    # Decrease chosen stat boost frrom battle state
    if stat_confirm == "atk":
        state.decrease_stat_boost("atk")
    elif stat_confirm == "def":
        state.decrease_stat_boost("def")
    
    #DEBUG
    print(f"[DEBUG]Final damage: {final_damage}")

    return final_damage


def get_type_effectiveness(defense_stats, attacker_type):
    atk_type_fixed = attacker_type.lower()

    return defense_stats[f'against_{atk_type_fixed}']