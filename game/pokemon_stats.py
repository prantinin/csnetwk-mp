# load stats from pokemon.csv

# load stats from pokemon.csv

# game/pokemon_stats.py
from chat.verbose_mode import VerboseManager
from dataclasses import dataclass
import csv
from typing import Dict, Optional
import os
import ast
from typing import List

print(os.getcwd())



@dataclass
class Pokemon:
    name: str
    type1: Optional[str]
    type2: Optional[str]
    hp: Optional[int]
    attack: Optional[int]
    defense: Optional[int]
    sp_attack: Optional[int]
    sp_defense: Optional[int]
    
    # Each type effectiveness as a separate field
    against_bug: float = 1.0
    against_dark: float = 1.0
    against_dragon: float = 1.0
    against_electric: float = 1.0
    against_fairy: float = 1.0
    against_fight: float = 1.0
    against_fire: float = 1.0
    against_flying: float = 1.0
    against_ghost: float = 1.0
    against_grass: float = 1.0
    against_ground: float = 1.0
    against_ice: float = 1.0
    against_normal: float = 1.0
    against_poison: float = 1.0
    against_psychic: float = 1.0
    against_rock: float = 1.0
    against_steel: float = 1.0
    against_water: float = 1.0
    
    raw: Dict[str, str] = None        #for debugging :), this will diplay other stats that will not be used for damage calculation



def _to_int(s: str) -> Optional[int]:
    if s is None or s.strip() == "":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None

def _to_float(s: str) -> Optional[float]:
    if s is None or s.strip() == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None

def _to_bool_from_int_str(s: str) -> bool:
    # expects '0' or '1'
    if s is None:
        return False
    s2 = s.strip().lower()
    return s2 in ("1", "true", "yes")

def _to_list(s: str) -> list:
    if not s or s.strip() == "":
        return []
    try:
        return ast.literal_eval(s)
    except:
        return []



def load_pokemon_stats(csv_path: str = None) -> Dict[str, Pokemon]:   #Loading of .csv file
    """Load CSV and return dict keyed by lowercase name -> Pokemon dataclass."""
    if csv_path is None:
        # Resolve CSV path relative to this file's location
        csv_path = os.path.join(os.path.dirname(__file__), "pokemon.csv")
    
    stats: Dict[str, Pokemon] = {}
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter=",")
        for row in reader:
            name = row.get("name", "").strip()
            if not name:
                continue

            #============= Pokemon stats to be taken ================
            p = Pokemon(
                name=name,
                type1=(row.get("type1") or "").strip() or None,
                type2=(row.get("type2") or "").strip() or None,
                hp=_to_int(row.get("hp")),
                attack=_to_int(row.get("attack")),
                defense=_to_int(row.get("defense")),
                sp_attack=_to_int(row.get("sp_attack")),
                sp_defense=_to_int(row.get("sp_defense")),

                # Type effectiveness columns
                against_bug=_to_int(row.get("against_bug")) or 1.0,
                against_dark=_to_int(row.get("against_dark")) or 1.0,
                against_dragon=_to_int(row.get("against_dragon")) or 1.0,
                against_electric=_to_int(row.get("against_electric")) or 1.0,
                against_fairy=_to_int(row.get("against_fairy")) or 1.0,
                against_fight=_to_int(row.get("against_fight")) or 1.0,
                against_fire=_to_int(row.get("against_fire")) or 1.0,
                against_flying=_to_int(row.get("against_flying")) or 1.0,
                against_ghost=_to_int(row.get("against_ghost")) or 1.0,
                against_grass=_to_int(row.get("against_grass")) or 1.0,
                against_ground=_to_int(row.get("against_ground")) or 1.0,
                against_ice=_to_int(row.get("against_ice")) or 1.0,
                against_normal=_to_int(row.get("against_normal")) or 1.0,
                against_poison=_to_int(row.get("against_poison")) or 1.0,
                against_psychic=_to_int(row.get("against_psychic")) or 1.0,
                against_rock=_to_int(row.get("against_rock")) or 1.0,
                against_steel=_to_int(row.get("against_steel")) or 1.0,
                against_water=_to_int(row.get("against_water")) or 1.0,

                raw=row
            )
            stats[name.lower()] = p
    return stats



def get_by_name(name: str, stats: Dict[str, Pokemon]) -> Optional[Pokemon]:
    if not name:
        return None
    return stats.get(name.strip().lower())

def pokemon_to_dict(pokemon: Pokemon) -> dict:
    """Return all Pokémon stats including type effectiveness columns as separate keys."""
    return {
        "name": pokemon.name,
        "type1": pokemon.type1,
        "type2": pokemon.type2,
        "hp": pokemon.hp,
        "attack": pokemon.attack,
        "defense": pokemon.defense,
        "sp_attack": pokemon.sp_attack,
        "sp_defense": pokemon.sp_defense,
        "against_bug": pokemon.against_bug,
        "against_dark": pokemon.against_dark,
        "against_dragon": pokemon.against_dragon,
        "against_electric": pokemon.against_electric,
        "against_fairy": pokemon.against_fairy,
        "against_fight": pokemon.against_fight,
        "against_fire": pokemon.against_fire,
        "against_flying": pokemon.against_flying,
        "against_ghost": pokemon.against_ghost,
        "against_grass": pokemon.against_grass,
        "against_ground": pokemon.against_ground,
        "against_ice": pokemon.against_ice,
        "against_normal": pokemon.against_normal,
        "against_poison": pokemon.against_poison,
        "against_psychic": pokemon.against_psychic,
        "against_rock": pokemon.against_rock,
        "against_steel": pokemon.against_steel,
        "against_water": pokemon.against_water,
    }


# quick CLI test
if __name__ == "__main__":
    import pprint, sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "game/pokemon.csv"
    stats = load_pokemon_stats(csv_path)
    print(f"Loaded {len(stats)} Pokémon.")