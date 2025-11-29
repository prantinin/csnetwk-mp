# turn order logic, game state tracking

    """_summary_
    ATTACK_ANNOUNCE -> allow sending only if it's the attacker's turn and phase is WAITING_FOR_ATTACK
    DEFENSE_ANNOUNCE -> move to CALCULATION phase after receiving this
    CALCULATION_REPORT -> wait for both sides' reports, update HP, check for win
    CALCULATION_CONFIRM -> Once both sides confirm, move to next turn
    GAME_OVER -> if HP <= 0, create and send this message
    """

# SETUP (Initial State)
    #host and joiner peers connect via handshake
    #host sends HANDSHAKE_RESPONSE with seed, both peers use this seed for the random num generator (for their stats)
    #both player peers send BATTLE_SETUP with chosen pokemon data and desired communication_mode
    #after exchanging BATTLE_SETUP, each transitions to WAITING_FOR_MOVE
    #spectators upon connecting receive all messages but do not take turns

# WAITING_FOR_MOVE (Turn-based State)
    #host peer first, acting peer sends ATTACK_ANNOUNCE with new sequence number
    #defending peer wait for ATTACK_ANNOUNCE, after receiving, defender sends DEFENSE_ANNOUNCE with signal ready for next phase
    # receiving DEFENSE_ANNOUNCE, both players independently apply damage and transition to PROCESSING_TURN

# PROCESSING_TURN (Turn processing State)
    #each player performs damage calculation using attack and defense stats based on damage_category
    #each player sends CALCULATION_REPORT with new sequence number to other player -> ACKs as checksum
    # insert discrepancy resolution (not my part)

# GAME_OVER (Final State)
    # when pokemon HP drops to zero or below, peer whose opponent has fainted sends GAME_OVER
    # message also requires sequence number and acknowledgment
    # receiving this message, battle ends

