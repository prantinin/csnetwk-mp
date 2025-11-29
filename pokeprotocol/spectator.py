from networking.message_parser import MessageParser
import socket

# GLOBAL VARIABLES AND CONSTANTS
HOST = "127.0.0.1"  # Host IP address
PORT = 65432        # Port used by host

divider = "=====================================\n\n"
parser = MessageParser()



# FUNCTIONS
def spectator_handshake():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        
        # Spectator connects to host
        print(f"[SPECTATOR] Connected to host at {HOST}:{PORT}")
        print(f"[SPECTATOR] Sending handshake request...\n")

        # Sending handshake request to host
        spectator_msg = "SPECTATOR_REQUEST"
        spectator_response = parser.encode_message({"message_type": spectator_msg})
        s.sendto(spectator_response.encode(), (HOST, PORT))

        data, addr = s.recvfrom(1024)
        host_msg = parser.decode_message(data.decode())
        message_type = host_msg.get("message_type")

        # Host handshake response handling
        if message_type == "HANDSHAKE_RESPONSE":
            print(host_msg)
            print(divider)
            print(f"[SPECTATOR] Handshake with host complete!\n")
            print("\n")
        else:
            print(f"[SPECTATOR] Unexpected message type: {message_type}")



# MAIN
spectator_handshake()