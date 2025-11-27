import socket
import random

HOST = "127.0.0.1"
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"[HOST] Listening on {HOST}:{PORT}")

while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode().strip()

    print(f"[HOST] Received from {addr}:\n{message}")

    # Check if it's a handshake request
    if message == "message_type: HANDSHAKE_REQUEST":
        seed = random.randint(1, 99999)

        response = (
            "message_type: HANDSHAKE_RESPONSE\n"
            f"seed: {seed}"
        )

        sock.sendto(response.encode(), addr)
        print(f"[HOST] Sent HANDSHAKE_RESPONSE with seed={seed} to {addr}")

        print("\nHandshake complete. Now ready for battle setup.\n")