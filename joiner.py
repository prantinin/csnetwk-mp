import socket

HOST = "127.0.0.1"
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send handshake request
request = "message_type: HANDSHAKE_REQUEST"
sock.sendto(request.encode(), (HOST, PORT))
print("[JOINER] Sent HANDSHAKE_REQUEST")

# Wait for response
data, addr = sock.recvfrom(1024)
response = data.decode()

print("[JOINER] Received:\n" + response)

# Parse the seed
lines = response.split("\n")
message_type = lines[0].split(": ")[1]
seed = int(lines[1].split(": ")[1])

if message_type == "HANDSHAKE_RESPONSE":
    print(f"[JOINER] Handshake successful! Received seed = {seed}")
else:
    print("[JOINER] Invalid handshake response")