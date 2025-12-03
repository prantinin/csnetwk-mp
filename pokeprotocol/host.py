from networking.message_parser import MessageParser
from game.battle_state import BattleState
from pokeprotocol.protocols import Protocols
import socket
import random



# GLOBAL VARIABLES AND CONSTANTS
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

parser = MessageParser()
protocols = Protocols()

divider = "========================================\n"
top_divider = "================== HOST ================\n"
init_divider = "=============== INITIALIZATION ===========\n"
battle_setup_divider = "=============== BATTLE SETUP ===========\n"
your_turn_divider = "================== YOUR TURN ==============\n"
their_turn_divider = "================== OPPONENT'S TURN =======\n"


# Initialize host
def init():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        
        # Host handshake initiation
        print('\n' + init_divider)
        print(f"[HOST] Host listening on {HOST}:{PORT}...")
        print(f"[HOST] Awaiting handshake...\n")

        # Receives data from client until termination via empty bytes object b''
        while True:
            data, addr = s.recvfrom(1024)
            client_msg = parser.decode_message(data.decode())
            message_type = client_msg.get("message_type")

            # Handshake response to joiner and spectator
            if message_type == "HANDSHAKE_REQUEST" or message_type == "SPECTATOR_REQUEST":
                if message_type == "HANDSHAKE_REQUEST":
                    role = "Joiner"
                else:
                    role = "Spectator"

                # Handshake response + seed generation
                print(f"[HOST] {role} handshake request received from {addr}\n")

                seed = random.randint(0, 9999)
                host_response = parser.encode_message({
                    "message_type": "HANDSHAKE_RESPONSE",
                    "seed": seed
                })
                s.sendto(host_response.encode(), addr)

                print(f"[HOST] seed generated: {seed}")
                print(f"[HOST] Handshake with {role} complete!\n\n")

                # Initialize battle if joiner connected
                if message_type == "HANDSHAKE_REQUEST":
                    print(battle_setup_divider)
                    
                    # Battle setup initiation
                    print(f"Initializing battle setup...\n")

                    # Sending host battle setup data
                    battle_data = protocols.host_battle_setup()
                    host_response = parser.encode_message({
                        "message_type": "BATTLE_SETUP",
                        "battle_data": battle_data
                    })
                    s.sendto(host_response.encode(), addr)
                    print("\nBattle setup data sent to Joiner. Awaiting Joiner response...\n")

                    # Receiving joiner battle setup data
                    data, addr = s.recvfrom(1024)
                    joiner_msg = parser.decode_message(data.decode())
                    print(f"\n\nBattle setup data received from Joiner:\n{joiner_msg}\n")
                    print("Battle setup data exchange complete! Battle initialization complete!\n")

                    # Initialize battle state
                    battle_state = BattleState(is_host=True, seed=seed, verbose=True)
                    joiner_raw_battle_data = joiner_msg['battle_data']
                    opp_battle_data = joiner_raw_battle_data['pokemon_name']
                    battle_state.set_pokemon_data(battle_data['pokemon_name'], opp_battle_data)
                    print('\n')

                    # Start game
                    protocols.start_game(s, addr, battle_state)

            else:
                print(f"[HOST] Unexpected message type: {message_type}")
                break



# MAIN

init()