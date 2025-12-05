from networking.message_parser import MessageParser
from game.battle_state import BattleState
from pokeprotocol.protocols import Protocols
import socket



# GLOBAL VARIABLES AND CONSTANTS
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

parser = MessageParser()
protocols = Protocols()

divider = "========================================\n"
top_divider = "================== JOINER ================\n"
init_divider = "=============== INITIALIZATION ===========\n"
battle_setup_divider = "=============== BATTLE SETUP ===========\n"
your_turn_divider = "================== YOUR TURN ==============\n"
their_turn_divider = "================== OPPONENT'S TURN =======\n"


# Initialize joiner
def init():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        
        # Joiner connects to host
        print(init_divider)
        print(f"[JOINER] Connected to host at {HOST}:{PORT}")
        print(f"[JOINER] Sending handshake request...\n")

        # Sending handshake request to host
        joiner_response = parser.encode_message({"message_type": "HANDSHAKE_REQUEST"})
        s.sendto(joiner_response.encode(), (HOST, PORT))

        while True:
            data, addr = s.recvfrom(1024)
            host_msg = parser.decode_message(data.decode())
            message_type = host_msg.get("message_type")

            # Host handshake response handling
            if message_type == "HANDSHAKE_RESPONSE":
                seed = host_msg['seed']
                print(f"[JOINER] Host message received:\n{host_msg}\n")
                print("[JOINER] Handshake with host complete!\n\n")

                # Battle setup initiation from host
                print(battle_setup_divider)
                
                print("Initializing battle setup...")
                print("Awaiting host battle setup data...\n")

            elif message_type == "BATTLE_SETUP":

                # Sending host battle setup data
                battle_data = protocols.joiner_battle_setup()
                host_response = parser.encode_message({
                    "message_type": "BATTLE_SETUP",
                    "battle_data": battle_data
                }) 
                s.sendto(host_response.encode(), addr)
                print("\nBattle setup data sent to Host. Battle initialization complete!\n\n")

                # Initialize battle state
                battle_state = BattleState(is_host=False, seed=seed, verbose=True)
                host_raw_battle_data = host_msg['battle_data']
                opp_battle_data = host_raw_battle_data['pokemon']
                battle_state.set_pokemon_data(battle_data['pokemon'], opp_battle_data, battle_data['stat_boosts'])
                print('\n')

                # Start game
                protocols.start_game(s, addr, battle_state)

            else:
                print(f"[JOINER] Unexpected message type: {message_type}")



# MAIN
init()