from networking.message_parser import MessageParser
import socket
import random



# GLOBAL VARIABLES AND CONSTANTS
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

parser = MessageParser()
divider = "========================================\n"
top_divider = "================== HOST ================\n"



# FUNCTIONS

# Initialize battle setup
def init_battle():
    pokemon = input("Choose your Pokemon: ")
    s_atk = input("How much special attack boost? ")
    s_def = input("How much special defense boost? ")

    return parser.encode_message({
        "pokemon": pokemon,
        "s_atk": s_atk,
        "s_def": s_def
    })


# Initialize host
def init():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        
        # Host handshake initiation
        print(divider)
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
                print(f"[HOST] Handshake with {role} complete!\n")

                # Initialize battle if joiner connected
                if message_type == "HANDSHAKE_REQUEST":
                    print(top_divider)
                    
                    # Battle setup initiation
                    print(f"Initializing battle setup...\n")

                    # Sending host battle setup data
                    poke_data = init_battle()
                    host_response = parser.encode_message({
                        "message_type": "BATTLE_SETUP",
                        "battle_data": poke_data
                    })
                    s.sendto(host_response.encode(), addr)

                    # Receiving joiner battle setup data
                    data, addr = s.recvfrom(1024)
                    joiner_msg = parser.decode_message(data.decode())
                    print(f"Battle setup data received from Joiner:\n{joiner_msg}")
                    print("\n")
                    print(divider)

            else:
                print(f"[HOST] Unexpected message type: {message_type}")
                break



# MAIN

init()