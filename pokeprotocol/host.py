# pokeprotocol/host.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from networking.message_parser import MessageParser
from game.battle_state import BattleState
from pokeprotocol.protocols import Protocols
from chat.chat_handler import ChatHandler
from networking.udp import ReliableUDP
from chat.verbose_mode import VerboseManager

import socket
import random

HOST = "127.0.0.1"
PORT = 65432
BUFFER_SIZE = 65535  # big enough for base64 stickers

init_divider = "=============== INITIALIZATION ===========\n"
battle_setup_divider = "=============== BATTLE SETUP ===========\n"


def send_ack(sock: socket.socket, addr, seq: int, parser: MessageParser):
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
    parser: MessageParser,
):
    """
    For host: handle ACK and CHAT_MESSAGE, forward others to caller.
    Returns:
        - None if the message was handled here (chat/ACK).
        - msg (dict) if it is a non-chat, non-ACK message.
    """
    mtype = msg.get("message_type")

    if mtype == "ACK":
        # ACKs are for the other side's ReliableUDP; we can ignore.
        return None

    if mtype == "CHAT_MESSAGE":
        seq = msg.get("sequence_number")
        if seq is not None:
            send_ack(sock, addr, seq, parser)
        if chat_handler is not None:
            chat_handler.handle_incoming(msg)
        else:
            sender = msg.get("sender_name", "Unknown")
            text = msg.get("message_text", "")
            print(f"[CHAT] {sender}: {text}")
        return None

    return msg


def init():
    parser = MessageParser()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            s.bind((HOST, PORT))
            break
        except OSError:
            retry_count += 1
            if retry_count < max_retries:
                print(f"[HOST] Port {PORT} in use, retrying... (attempt {retry_count}/{max_retries})")
                import time
                time.sleep(1)
            else:
                s.close()
                print(f"[HOST] Failed to bind after {max_retries} attempts. Exiting.")
                raise
    
    with s:
        print("\n" + init_divider)
        print(f"[HOST] Host listening on {HOST}:{PORT}...")
        print("[HOST] Awaiting handshake...\n")

        reliable = ReliableUDP(
            socket_obj=s,
            parser=parser,
            timeout=0.5,
            max_retries=3,
            loss_prob=0.0,
            verbose=True,
        )
        
        protocols = Protocols(reliable)

        chat_handler = None
        joiner_addr = None
        battle_state = None

        # === HANDSHAKE LOOP ===
        while True:
            data, addr = s.recvfrom(BUFFER_SIZE)
            msg = parser.decode_message(data.decode("utf-8"))
            message_type = msg.get("message_type")

            # handle chat or ACK even before joiner is fully set up
            if message_type in ("CHAT_MESSAGE", "ACK"):
                handled = handle_incoming_with_chat(s, addr, msg, chat_handler, parser)
                if handled is None:
                    continue

            if message_type not in ("HANDSHAKE_REQUEST", "SPECTATOR_REQUEST"):
                print(f"[HOST] Unexpected message type in init: {message_type}")
                continue

            if message_type == "HANDSHAKE_REQUEST":
                role = "Joiner"
                print(f"[HOST] {role} handshake request received from {addr}\n")
                if VerboseManager.is_verbose():
                    print(f"[DBUG:HOST] Handshake from address: {addr}")

                seed = random.randint(0, 9999)
                resp = {
                    "message_type": "HANDSHAKE_RESPONSE",
                    "seed": seed,
                }
                s.sendto(parser.encode_message(resp).encode("utf-8"), addr)
                if VerboseManager.is_verbose():
                    print(f"[DBUG:HOST] Sent HANDSHAKE_RESPONSE with seed={seed}")

                print(f"[HOST] seed generated: {seed}")
                print(f"[HOST] Handshake with {role} complete!\n")

                joiner_addr = addr

                # Create ChatHandler now that we know the peer
                chat_handler = ChatHandler(
                    socket_obj=s,
                    my_name="HOST",
                    peer_addr=joiner_addr,
                    reliable=reliable,
                    verbose=True,
                )
                protocols.attach_chat_handler(chat_handler)

                # === BATTLE SETUP ===
                print(battle_setup_divider)
                print("Initializing battle setup...\n")
                if VerboseManager.is_verbose():
                    print("[DBUG:HOST] Starting battle setup phase")

                # host chooses pokemon, etc. (host_battle_setup should use input_with_chat)
                battle_data = protocols.host_battle_setup()
                if VerboseManager.is_verbose():
                    print(f"[DBUG:HOST] Host battle data prepared: {battle_data.get('pokemon_name', 'Unknown')}")

                host_setup_msg = {
                    "message_type": "BATTLE_SETUP",
                    "battle_data": battle_data,
                }
                s.sendto(
                    parser.encode_message(host_setup_msg).encode("utf-8"),
                    joiner_addr,
                )
                if VerboseManager.is_verbose():
                    print(f"[DBUG:HOST] Sent BATTLE_SETUP message to {joiner_addr}")
                print("\nBattle setup data sent to Joiner. Awaiting Joiner response...\n")

                # wait for joiner BATTLE_SETUP (still handling chat)
                while True:
                    data2, addr2 = s.recvfrom(BUFFER_SIZE)
                    msg2 = parser.decode_message(data2.decode("utf-8"))

                    handled2 = handle_incoming_with_chat(s, addr2, msg2, chat_handler, parser)
                    if handled2 is None:
                        continue

                    if handled2.get("message_type") != "BATTLE_SETUP":
                        print(
                            f"[HOST] Unexpected message type during battle setup: "
                            f"{handled2.get('message_type')}"
                        )
                        continue

                    joiner_msg = handled2
                    break

                print("\nBattle setup data received from Joiner:")
                print(joiner_msg)
                print(
                    "\nBattle setup data exchange complete! "
                    "Battle initialization complete!\n"
                )

                # Initialize BattleState
                battle_state = BattleState(is_host=True, seed=seed, verbose=True)
                if VerboseManager.is_verbose():
                    print(f"[DBUG:HOST] BattleState initialized for host with seed={seed}")
                joiner_raw = joiner_msg["battle_data"]
                opp_battle_data = joiner_raw["pokemon_name"]
                battle_state.set_pokemon_data(battle_data["pokemon_name"], opp_battle_data, battle_data["stat_boosts"])
                print(
                    f"\n[DBUG:HOST] Pokemon data set: "
                    f"Mine HP: {battle_state.my_pokemon['hp']} "
                    f"Opponent HP: {battle_state.opponent_pokemon['hp']}\n"
                )
                if VerboseManager.is_verbose():
                    print(f"[DBUG:HOST] Host pokemon: {battle_state.my_pokemon.get('name', '?')}, Opponent: {battle_state.opponent_pokemon.get('name', '?')}")

                # Done with init; break out to start game
                break

            else:
                # SPECTATOR_REQUEST – you can extend this if you want spectators
                print(f"[HOST] Spectator handshake received from {addr}")
                resp = {
                    "message_type": "HANDSHAKE_RESPONSE",
                    "seed": random.randint(0, 9999),
                }
                s.sendto(parser.encode_message(resp).encode("utf-8"), addr)
                # For simplicity we don't attach spectator chat here.

        # === GAME LOOP ===
        if battle_state is not None and joiner_addr is not None:
            protocols.start_game(s, joiner_addr, battle_state)
        else:
            print("[HOST] No battle_state created. Exiting.")


if __name__ == "__main__":
    init()
