import socket
import random

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

message_type = ""
divider = "=====================================\n\n"

def init():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        
        # Host handshake initiation
        print(f"[HOST] Host listening on {HOST}:{PORT}...")
        print(f"[HOST] Awaiting handshake...\n")

        # Receives data from client until termination via empty bytes object b''
        while True:
            data, addr = s.recvfrom(1024)
            joiner_msg = data.decode()

            if joiner_msg == "HANDSHAKE_REQUEST":
                print(f"[HOST] Handshake request received from {addr}")

                # Handshake response to joiner
                message_type = "HANDSHAKE_RESPONSE"
                seed = random.randint(0, 9999)
                host_response = f"{message_type}; {seed}"

                s.sendto(host_response.encode(), addr)
                print(f"[HOST] Handshake with joiner complete!\n")
                print(divider)

            else:
                print(f"[HOST] Unexpected message type: {joiner_msg}")
                break

init()