from game.battle_state import BattleState, GamePhase

def test_basic_flow():
    print("=== Testing Basic Battle Flow ===\n")
    
    # Setup
    host = BattleState(is_host=True, seed=12345, verbose=True)
    joiner = BattleState(is_host=False, seed=12345, verbose=True)
    
    # Set pokemon data
    host_pokemon = {'name': 'Pikachu', 'hp': 100}
    joiner_pokemon = {'name': 'Charmander', 'hp': 100}
    
    host.set_pokemon_data(host_pokemon.copy(), joiner_pokemon.copy())
    joiner.set_pokemon_data(joiner_pokemon.copy(), host_pokemon.copy())
    
    print("\n--- Turn 1: Host attacks ---")
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
    host.both_confirmed()
    joiner.both_confirmed()
    
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
    
    # Simulate fatal damage
    joiner.record_local_calculation(0)  # Joiner faints
    
    assert joiner.is_game_over() == True
    assert joiner.winner == "opponent"
    
    print("\n Game over test passed!")

if __name__ == "__main__":
    test_basic_flow()
    test_game_over()