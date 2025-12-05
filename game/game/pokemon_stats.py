# load stats from pokemon.csv

# load stats from pokemon.csv

# game/pokemon_stats.py
from dataclasses import dataclass
import csv
from typing import Dict, Optional
import os
print(os.getcwd())



@dataclass
class Pokemon:
    name: str
    pokedex_number: Optional[int]
    type1: Optional[str]
    type2: Optional[str]
    hp: Optional[int]
    attack: Optional[int]
    defense: Optional[int]
    sp_attack: Optional[int]
    sp_defense: Optional[int]
    speed: Optional[int]
    weight_kg: Optional[float]
    height_m: Optional[float]
    is_legendary: bool
    
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


def load_pokemon_stats(csv_path: str = "game/pokemon.csv") -> Dict[str, Pokemon]:   #Loading of .csv file
    """Load CSV and return dict keyed by lowercase name -> Pokemon dataclass."""
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
                pokedex_number=_to_int(row.get("pokedex_number")),
                type1=(row.get("type1") or "").strip() or None,
                type2=(row.get("type2") or "").strip() or None,
                hp=_to_int(row.get("hp")),
                attack=_to_int(row.get("attack")),
                defense=_to_int(row.get("defense")),
                sp_attack=_to_int(row.get("sp_attack")),
                sp_defense=_to_int(row.get("sp_defense")),
                speed=_to_int(row.get("speed")),
                weight_kg=_to_float(row.get("weight_kg")),
                height_m=_to_float(row.get("height_m")),
                is_legendary=_to_bool_from_int_str(row.get("is_legendary")),
                raw=row
            )
            stats[name.lower()] = p
    return stats



def get_by_name(name: str, stats: Dict[str, Pokemon]) -> Optional[Pokemon]:
    if not name:
        return None
    return stats.get(name.strip().lower())

def get_by_number(number: int, stats: Dict[str, Pokemon]) -> Optional[Pokemon]:
    for p in stats.values():
        if p.pokedex_number == number:
            return p
    return None

def pokemon_to_dict(self, pokemon):
    return {
        "name": pokemon.name,
        "type1": pokemon.type1,
        "type2": pokemon.type2,
        "hp": pokemon.hp,
        "attack": pokemon.attack,
        "defense": pokemon.defense,
        "special_attack": pokemon.sp_attack,
        "special_defense": pokemon.sp_defense,
        "speed": pokemon.speed
    }


# quick CLI test
if __name__ == "__main__":
    import pprint, sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "game/pokemon.csv"
    stats = load_pokemon_stats(csv_path)
    print(f"Loaded {len(stats)} Pokémon.")


