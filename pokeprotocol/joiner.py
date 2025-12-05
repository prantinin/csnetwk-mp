# pokeprotocol/joiner.py

from networking.message_parser import MessageParser
from game.battle_state import BattleState
from pokeprotocol.protocols import Protocols
from chat.chat_handler import ChatHandler
from networking.udp import ReliableUDP

import socket

HOST = "127.0.0.1"
PORT = 65432
BUFFER_SIZE = 65535

parser = MessageParser()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
reliable = ReliableUDP(sock, verbose=True)
protocols = Protocols(reliable)

init_divider = "=============== INITIALIZATION ===========\n"
battle_setup_divider = "=============== BATTLE SETUP ===========\n"


def send_ack(sock: socket.socket, addr, seq: int):
    ack = {
        "message_type": "ACK",
        "sequence_number": seq,
    }
    sock.sendto(parser.encode_message(ack).encode("utf-8"), addr)


def handle_incoming_with_chat(
    sock: socket.socket,
    addr,
    msg: dict,
    chat_handler: ChatHandler,
):
    """
    For joiner: handle ACK and CHAT_MESSAGE, forward others to caller.
    Returns:
        - None if handled here (chat/ACK)
        - msg dict if it is a non-chat, non-ACK message
    """
    mtype = msg.get("message_type")

    if mtype == "ACK":
        # ACK is meant for other side's ReliableUDP; ignore here.
        return None

    if mtype == "CHAT_MESSAGE":
        seq = msg.get("sequence_number")
        if seq is not None:
            send_ack(sock, addr, seq)
        if chat_handler is not None:
            chat_handler.handle_incoming(msg)
        else:
            sender = msg.get("sender_name", "Unknown")
            text = msg.get("message_text", "")
            print(f"[CHAT] {sender}: {text}")
        return None

    return msg


def init():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        print("\n" + init_divider)
        print(f"/Users/romaaguila/Desktop/csnetwk-mp-main\n")
        print(f"[JOINER] Connected to host at {HOST}:{PORT}")

        # IMPORTANT: we DO NOT call s.connect() here
        # so we can safely use sendto() with (HOST, PORT) and recvfrom().

        chat_handler = ChatHandler(
            socket_obj=s,
            my_name="JOINER",
            peer_addr=(HOST, PORT),
            reliable=reliable,
            verbose=True,
        )
        protocols.attach_chat_handler(chat_handler)

        print("[JOINER] Sending handshake request...\n")
        handshake_req = {
            "message_type": "HANDSHAKE_REQUEST",
        }
        s.sendto(
            parser.encode_message(handshake_req).encode("utf-8"),
            (HOST, PORT),
        )

        # === WAIT FOR HANDSHAKE_RESPONSE ===
        while True:
            data, addr = s.recvfrom(BUFFER_SIZE)
            msg = parser.decode_message(data.decode("utf-8"))

            handled = handle_incoming_with_chat(s, addr, msg, chat_handler)
            if handled is None:
                continue

            if handled.get("message_type") != "HANDSHAKE_RESPONSE":
                print(
                    f"[JOINER] Unexpected message type while waiting for handshake: "
                    f"{handled.get('message_type')}"
                )
                continue

            seed = handled["seed"]
            print("[JOINER] Host message received:")
            print(handled)
            print("\n[JOINER] Handshake with host complete!\n")
            break

        # === BATTLE SETUP ===
        print(battle_setup_divider)
        print("Initializing battle setup...")
        print("Awaiting host battle setup data...\n")

        host_battle_data = None

        # Wait for host's BATTLE_SETUP (while still handling chat)
        while True:
            data, addr = s.recvfrom(BUFFER_SIZE)
            msg = parser.decode_message(data.decode("utf-8"))

            handled = handle_incoming_with_chat(s, addr, msg, chat_handler)
            if handled is None:
                continue

            if handled.get("message_type") != "BATTLE_SETUP":
                print(
                    f"[JOINER] Unexpected message type while waiting for host setup: "
                    f"{handled.get('message_type')}"
                )
                continue

            print("[JOINER] Host battle setup data received:")
            print(handled)
            host_battle_data = handled["battle_data"]
            break

        print("\nHost setup received. Now choose your Pokémon.\n")

        # Joiner chooses Pokémon (this should use input_with_chat internally)
        joiner_battle_data = protocols.joiner_battle_setup()

        # Send our setup back to host
        joiner_setup_msg = {
            "message_type": "BATTLE_SETUP",
            "battle_data": joiner_battle_data,
        }
        s.sendto(
            parser.encode_message(joiner_setup_msg).encode("utf-8"),
            (HOST, PORT),
        )
        print("Battle setup data sent to Host.")
        print("Battle initialization complete!\n")

        # === Initialize BattleState ===
        battle_state = BattleState(is_host=False, seed=seed, verbose=True)
        my_poke_data = joiner_battle_data["pokemon_name"]
        opp_poke_data = host_battle_data["pokemon_name"]
        battle_state.set_pokemon_data(my_poke_data, opp_poke_data)

        print(
            f"[DBUG:JOINER] Pokemon data set: "
            f"Mine HP: {battle_state.my_pokemon['hp']} "
            f"Opponent HP: {battle_state.opponent_pokemon['hp']}\n"
        )

        # === GAME LOOP ===
        protocols.start_game(s, (HOST, PORT), battle_state)


if __name__ == "__main__":
    init()
