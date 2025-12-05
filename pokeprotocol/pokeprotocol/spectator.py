from networking.message_parser import MessageParser
from chat.chat_handler import ChatHandler

import socket

HOST = "127.0.0.1"
PORT = 65432

parser = MessageParser()

init_divider = "=============== INITIALIZATION ===========\n"


def init():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        print("\n" + init_divider)
        print(f"[SPECTATOR] Connecting to host at {HOST}:{PORT}")
        s.connect((HOST, PORT))

        # --------- HANDSHAKE ---------
        handshake_msg = parser.encode_message({"message_type": "SPECTATOR_REQUEST"})
        s.send(handshake_msg.encode())
        print("[SPECTATOR] Sending spectator handshake request...\n")

        data = s.recv(1024)
        host_msg = parser.decode_message(data.decode())
        if host_msg.get("message_type") != "HANDSHAKE_RESPONSE":
            print("[SPECTATOR] Unexpected handshake response:", host_msg)
            return

        print("[SPECTATOR] Handshake with host complete! Now listening...\n")

        # For now, spectator is receive-only. We still use ChatHandler to pretty-print chat.
        chat = ChatHandler(
            socket_obj=s,
            my_name="SPECTATOR",
            peer_addr=(HOST, PORT),
            reliable=None,
            verbose=False,
        )

        # --------- MAIN RECEIVE LOOP ---------
        while True:
            data = s.recv(4096)
            msg = parser.decode_message(data.decode())
            mtype = msg.get("message_type")

            if mtype == "CHAT_MESSAGE":
                chat.handle_incoming(msg)
            else:
                # Just print battle-related messages for now
                print(f"[SPECTATOR] Received: {msg}")


if __name__ == "__main__":
    init()
