# damage formulas and win/loss check 
#Added Type Effectiveness

""" Not yet integrated into battle_state.py"""



from pokemon_stats import get_by_name

def get_type_effectiveness(move_type, defender_type1, defender_type2):
    # Primary
    eff1 = TYPE_CHART.get(move_type, {}).get(defender_type1, 1.0)
    # Secondary
    eff2 = TYPE_CHART.get(move_type, {}).get(defender_type2, 1.0) if defender_type2 else 1.0
    return eff1 * eff2


def get_type_multiplier(move_type: str, defender):
    """Multiply effectiveness vs defender.type1 and defender.type2."""
    t1 = TYPE_EFFECTIVENESS.get((move_type, defender.type1), 1.0)
    t2 = 1.0
    if defender.type2:
        t2 = TYPE_EFFECTIVENESS.get((move_type, defender.type2), 1.0)
    return t1 * t2



#------------------------ Damage Calculation -----------------------------------------------
def calculate_damage(attacker: dict, defender: dict, move: dict, stat_boosts: dict):
    """Calculate damage with debug info."""
    base_power = move.get("base_power", 1.0)
    move_type = move.get("type", "Normal")
    category = move.get("damage_category", "physical")

    if category == "physical":
        atk_stat = attacker.get("attack", 10)
        def_stat = defender.get("physical_defense", 10)
    else:
        atk_stat = attacker.get("special_attack", 10)
        def_stat = defender.get("special_defense", 10)
        if stat_boosts.get("special_attack_uses", 0) > 0:
            atk_stat *= 1.5
            stat_boosts["special_attack_uses"] -= 1
            print(f"[DEBUG] {attacker.get('name')} special attack boosted: {atk_stat}")
        if stat_boosts.get("special_defense_uses", 0) > 0:
            def_stat *= 1.5
            stat_boosts["special_defense_uses"] -= 1
            print(f"[DEBUG] {defender.get('name')} special defense boosted: {def_stat}")

    type_eff = get_type_effectiveness(move_type, defender.get("type1"), defender.get("type2"))
    print(f"[DEBUG] Move Type: {move_type}, Defender Types: {defender.get('type1')}/{defender.get('type2')}, Effectiveness: {type_eff}")

    damage = (base_power * atk_stat * type_eff) / max(def_stat, 1)
    final_damage = max(1, int(damage))
    print(f"[DEBUG] Base Power: {base_power}, Atk: {atk_stat}, Def: {def_stat}, Damage: {final_damage}")

    return final_damage, type_eff

#--------------------------- Battle Loop ---------------------------------------------
def battle_loop(p1, p2, moveset1, moveset2):
    """
    Turn-based fight between two Pokémon objects.
    """
    print(f"\nBattle Start! {p1.name} vs {p2.name}\n")

    while p1.hp > 0 and p2.hp > 0:

        # Player 1 attacks Player 2
        m1 = moveset1[0]  # pick first move for now
        dmg, eff = calculate_damage(p1, p2, m1, {"special_attack_uses": 0, "special_defense_uses": 0})
        p2.hp -= dmg
        print(f"[DEBUG] {p1.name} used {m1['name']}! Damage: {dmg}, Type Effectiveness: {eff}, {p2.name} HP left: {p2.hp}")

        if p2.hp <= 0:
            print(f"\n{p2.name} fainted! {p1.name} wins!")
            break

        # Player 2 attacks Player 1
        m2 = moveset2[0]
        dmg, eff = calculate_damage(p2, p1, m2, {"special_attack_uses": 0, "special_defense_uses": 0})
        p1.hp -= dmg
        print(f"[DEBUG] {p2.name} used {m2['name']}! Damage: {dmg}, Type Effectiveness: {eff}, {p1.name} HP left: {p1.hp}")

        if p1.hp <= 0:
            print(f"\n{p1.name} fainted! {p2.name} wins!")
            break
        
def process_turn(self):
    """
    Called when: 
    - ATTACK_ANNOUNCE received
    - DEFENSE_ANNOUNCE received 
    - Both peers now compute the turn locally
    """

    if not self.last_attack:
        self.log("ERROR: No attack data to process.")
        return

    move = self.last_attack["move"]          # {name, type, damage_category, base_power}
    attacker_is_me = self.my_turn

    attacker = self.my_pokemon if attacker_is_me else self.opponent_pokemon
    defender = self.opponent_pokemon if attacker_is_me else self.my_pokemon

    stat_boosts = self.last_attack["stat_boosts"]  # shared

    damage, eff = self.calculate_damage(attacker, defender, move, stat_boosts)

    # apply damage locally
    new_hp = max(0, defender["hp"] - damage)

    # store in battle_state for reporting
    if attacker_is_me:
        self.record_local_calculation(new_hp)
    else:
        self.receive_calculation_report(new_hp, self.sequence_number)

    self.log(f"{attacker['name']} used {move['name']} | Damage={damage} | Effectiveness={eff}")

        


# --------------------TYPE EFFECTIVENESS CHART ---------------
TYPE_CHART = {
    "Normal":    {"Rock":0.5, "Ghost":0.0, "Steel":0.5},
    "Fire":      {"Fire":0.5, "Water":0.5, "Grass":2.0, "Ice":2.0, "Bug":2.0, "Rock":0.5, "Dragon":0.5, "Steel":2.0},
    "Water":     {"Fire":2.0, "Water":0.5, "Grass":0.5, "Ground":2.0, "Rock":2.0, "Dragon":0.5},
    "Electric":  {"Water":2.0, "Electric":0.5, "Grass":0.5, "Ground":0.0, "Flying":2.0, "Dragon":0.5},
    "Grass":     {"Fire":0.5, "Water":2.0, "Grass":0.5, "Poison":0.5, "Ground":2.0, "Flying":0.5, "Bug":0.5, "Rock":2.0, "Dragon":0.5, "Steel":0.5},
    "Ice":       {"Fire":0.5, "Water":0.5, "Grass":2.0, "Ground":2.0, "Flying":2.0, "Dragon":2.0, "Steel":0.5},
    "Fighting":  {"Normal":2.0, "Ice":2.0, "Rock":2.0, "Dark":2.0, "Steel":2.0, "Poison":0.5, "Flying":0.5, "Psychic":0.5, "Bug":0.5, "Ghost":0.0, "Fairy":0.5},
    "Poison":    {"Grass":2.0, "Poison":0.5, "Ground":0.5, "Rock":0.5, "Ghost":0.5, "Steel":0.0, "Fairy":2.0},
    "Ground":    {"Fire":2.0, "Electric":2.0, "Poison":2.0, "Rock":2.0, "Steel":2.0, "Grass":0.5, "Bug":0.5, "Flying":0.0},
    "Flying":    {"Grass":2.0, "Electric":0.5, "Fighting":2.0, "Bug":2.0, "Rock":0.5, "Steel":0.5},
    "Psychic":   {"Fighting":2.0, "Poison":2.0, "Psychic":0.5, "Dark":0.0, "Steel":0.5},
    "Bug":       {"Grass":2.0, "Psychic":2.0, "Dark":2.0, "Fire":0.5, "Fighting":0.5, "Poison":0.5, "Flying":0.5, "Ghost":0.5, "Steel":0.5, "Fairy":0.5},
    "Rock":      {"Fire":2.0, "Ice":2.0, "Flying":2.0, "Bug":2.0, "Fighting":0.5, "Ground":0.5, "Steel":0.5},
    "Ghost":     {"Psychic":2.0, "Ghost":2.0, "Dark":0.5, "Normal":0.0},
    "Dragon":    {"Dragon":2.0, "Steel":0.5, "Fairy":0.0},
    "Dark":      {"Psychic":2.0, "Ghost":2.0, "Fighting":0.5, "Dark":0.5, "Fairy":0.5},
    "Steel":     {"Ice":2.0, "Rock":2.0, "Fairy":2.0, "Fire":0.5, "Water":0.5, "Electric":0.5, "Steel":0.5},
    "Fairy":     {"Fighting":2.0, "Dragon":2.0, "Dark":2.0, "Fire":0.5, "Poison":0.5, "Steel":0.5},
}
        
