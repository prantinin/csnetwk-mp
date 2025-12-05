# damage formulas and win/loss check 
#Added Type Effectiveness

""" Not yet integrated into battle_state.py"""


from game.battle_state import BattleState
from chat.verbose_mode import VerboseManager
from game.pokemon_stats import get_by_name, pokemon_to_dict

#------------------------ Damage Calculation -----------------------------------------------
def calculate_damage(state: BattleState, stat_confirm, your_turn):
    """Calculate damage with debug info."""
    if VerboseManager.is_verbose():
        print(f"[DAMAGE_CALC] Calculating damage. your_turn={your_turn}, stat_confirm={stat_confirm}")

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
    if VerboseManager.is_verbose():
        print(f"[DAMAGE_CALC] Attacker: {attacker.get('name', '?')}, Defender: {defender.get('name', '?')}")

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
    
    # Getting attacker's type effectiveness against defender
    type1_eff = get_type_effectiveness(defender, attacker['type1'])

    if attacker['type2'] != None:
        type2_eff = get_type_effectiveness(defender, attacker['type2'])
    else:
        type2_eff = 1.0
    
    # Actual damage calculation
    damage = (base_power * atk_stat * type1_eff * type2_eff) / max(def_stat, 1)
    variance = state.rng.uniform(0.85, 1.0)
    final_damage = max(1, int(damage * variance))
    if VerboseManager.is_verbose():
        print(f"[DAMAGE_CALC] Base damage: {damage:.2f}, Type effectiveness: {type1_eff} x {type2_eff}, Variance: {variance:.2f}")
        print(f"[DAMAGE_CALC] Final damage: {final_damage}")

    # Settling damage effect message
    effect = get_damage_effect(defender['hp'], final_damage)

    return final_damage, effect


def get_type_effectiveness(defense_stats, attacker_type):
    atk_type_fixed = attacker_type.lower()

    return defense_stats[f'against_{atk_type_fixed}']

def get_damage_effect(orig_hp, damage):
    ratio = damage/orig_hp
    if VerboseManager.is_verbose():
        print(f"[DAMAGE_CALC] Damage ratio: {ratio:.2f} (damage={damage}, orig_hp={orig_hp})")

    if ratio >= 0.9:
        effect = "super effective"
    elif ratio < 0.9 and ratio >= 0.6:
        effect = "very effective"
    elif ratio < 0.6 and ratio >= 0.3:
        effect = "effective"
    else:
        effect = "not very effective"

    return effect