from networking.message_parser import MessageParser
import socket

# GLOBAL VARIABLES AND CONSTANTS
HOST = "127.0.0.1"  # Host IP address
PORT = 65432        # Port used by host

divider = "==========================================\n\n"
top_divider = "================== JOINER ================\n\n"
parser = MessageParser()



# FUNCTIONS

# Initialize battle setup
def init_battle():
    pokemon = input("\nChoose your Pokemon: ")
    s_atk = input("How much special attack boost? ")
    s_def = input("How much special defense boost? ")

    return parser.encode_message({
        "pokemon": pokemon,
        "s_atk": s_atk,
        "s_def": s_def
    })

# Initialize joiner
def joiner_handshake():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        
        # Joiner connects to host
        print(divider)
        print(f"[JOINER] Connected to host at {HOST}:{PORT}")
        print(f"[JOINER] Sending handshake request...\n")

        # Sending handshake request to host
        joiner_msg = "HANDSHAKE_REQUEST"
        joiner_response = parser.encode_message({"message_type": joiner_msg})
        s.sendto(joiner_response.encode(), (HOST, PORT))

        while True:
            data, addr = s.recvfrom(1024)
            host_msg = parser.decode_message(data.decode())
            message_type = host_msg.get("message_type")

            # Host handshake response handling
            if message_type == "HANDSHAKE_RESPONSE":
                print(f"[JOINER] Host message received:\n{host_msg}\n")
                print(f"[JOINER] Handshake with host complete!")
                print("\n")
            elif message_type == "BATTLE_SETUP":
                print(top_divider)
                
                # Battle setup initiation from host
                print(f"Initializing battle setup...\n")
                host_msg = parser.decode_message(data.decode())
                print(f"\nBattle setup data received from Host:\n{host_msg}")

                # Sending host battle setup data
                poke_data = init_battle()
                host_response = parser.encode_message({
                    "message_type": "BATTLE_SETUP",
                    "battle_data": poke_data
                })
                s.sendto(host_response.encode(), addr)
            else:
                break
            
        else:
            print(f"[JOINER] Unexpected message type: {message_type}")



# MAIN
joiner_handshake()