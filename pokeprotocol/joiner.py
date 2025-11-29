import socket

HOST = "127.0.0.1"  # Host IP address
PORT = 65432        # Port used by host

message_type = ""
divider = "=====================================\n\n"

def joiner_handshake():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        
        # Joiner connects to host
        print(f"[JOINER] Connected to host at {HOST}:{PORT}")
        print(f"[JOINER] Sending handshake request...\n")

        # Sending handshake request to host
        message_type = "HANDSHAKE_REQUEST"
        s.sendto(message_type.encode(), (HOST, PORT))

        data, addr = s.recvfrom(1024)
        host_response = data.decode()
        host_msg, seed = host_response.split("; ")

        # Host handshake response handling
        if host_msg == "HANDSHAKE_RESPONSE":
            print(f"[JOINER] Handshake with host complete!\n")
            print(f"[JOINER] message_type: {host_msg}")
            print(f"[JOINER] seed: {seed}\n")
            print(divider)
        else:
            print(f"[JOINER] Unexpected message type: {host_msg}")


joiner_handshake()