from game.battle_state import BattleState, GamePhase

def test_basic_flow():
    print("=== Testing Basic Battle Flow ===\n")
    
    # Setup - start with verbose OFF
    host = BattleState(is_host=True, seed=12345, verbose=False)
    joiner = BattleState(is_host=False, seed=12345, verbose=False)
    
    # Set pokemon data
    host_pokemon = {'name': 'Pikachu', 'hp': 100}
    joiner_pokemon = {'name': 'Charmander', 'hp': 100}
    
    host.set_pokemon_data(host_pokemon.copy(), joiner_pokemon.copy())
    joiner.set_pokemon_data(joiner_pokemon.copy(), host_pokemon.copy())
    
    print("\n--- Turn 1: Host attacks (verbose OFF) ---")
    # Host attacks
    assert host.can_attack() == True
    assert joiner.can_defend() == True
    
    attack_data = {'move': 'Thunderbolt', 'damage': 30}
    joiner.receive_attack_announce(attack_data)
    
    # Both receive defense announce
    host.receive_defense_announce()
    joiner.receive_defense_announce()
    
    assert host.current_phase == GamePhase.PROCESSING_TURN
    assert joiner.current_phase == GamePhase.PROCESSING_TURN
    
    # Turn ON verbose to see the calculation phase
    print("\n--- Enabling verbose for calculation phase ---")
    host.set_verbose(True)
    joiner.set_verbose(True)
    
    # Calculate damage
    joiner.record_local_calculation(70)  # Joiner takes 30 damage
    host.record_local_calculation(100)   # Host takes no damage
    
    # Exchange calculation reports
    host.receive_calculation_report(70, 1)
    joiner.receive_calculation_report(100, 1)
    
    # Confirm calculations
    host.send_calculation_confirm()
    joiner.send_calculation_confirm()
    
    host.receive_calculation_confirm()
    joiner.receive_calculation_confirm()
    
    # Check turn switch
    assert host.both_confirmed() == True
    assert joiner.both_confirmed() == True
    
    host.switch_turn()
    joiner.switch_turn()
    
    assert host.my_turn == False
    assert joiner.my_turn == True
    assert host.current_phase == GamePhase.WAITING_FOR_MOVE
    
    print("\n--- Turn 2: Joiner attacks ---")
    # Joiner's turn
    assert joiner.can_attack() == True
    assert host.can_defend() == True
    
    print("\n All tests passed!")

def test_game_over():
    print("\n=== Testing Game Over ===\n")
    
    host = BattleState(is_host=True, seed=12345, verbose=True)
    joiner = BattleState(is_host=False, seed=12345, verbose=True)
    
    host.set_pokemon_data({'hp': 100}, {'hp': 10})
    joiner.set_pokemon_data({'hp': 10}, {'hp': 100})
    
    # Update joiner's pokemon HP to 0
    joiner.my_pokemon['hp'] = 0
    
    # Simulate fatal damage
    joiner.record_local_calculation(0)  # Joiner faints
    
    assert joiner.is_game_over() == True
    assert joiner.winner == "opponent"
    
    print("\n Game over test passed!")

def test_verbose_toggle():
    print("\n=== Testing Verbose Toggle ===\n")
    
    # Start with verbose OFF
    print("--- TEST 1: Verbose=False (should see NO debug messages) ---")
    battle = BattleState(is_host=True, seed=12345, verbose=False)
    battle.log("This should NOT print (verbose is OFF)")
    battle.set_pokemon_data({'hp': 100}, {'hp': 100})
    battle.next_sequence_number()
    battle.can_attack()
    battle.record_local_calculation(100)
    print("   ^^ No debug messages above? Good!\n")
    
    # Turn verbose ON
    print("--- TEST 2: Verbose=True (SHOULD see debug messages) ---")
    battle.set_verbose(True)
    battle.log("This SHOULD print (verbose is now ON)")
    battle.set_pokemon_data({'hp': 100}, {'hp': 100})
    battle.next_sequence_number()
    battle.can_attack()
    battle.record_local_calculation(100)
    print("   ^^ Debug messages appeared above? Good!\n")
    
    print(" Verbose toggle test passed!")

if __name__ == "__main__":
    test_verbose_toggle()
    test_basic_flow()
    test_game_over()