"""
Sandbox tests for Roma's parts:

- MessageParser (key: value)
- BattleState discrepancy helpers
- ChatHandler (text + sticker saving)
- ReliableUDP helpers (sequence, duplicates)
"""

import os
import base64

from networking.message_parser import MessageParser
from networking.udp import ReliableUDP
from chat.chat_handler import ChatHandler
from game.battle_state import BattleState


# ---------- MESSAGE PARSER TEST ----------

def test_message_parser():
    print("=== test_message_parser ===")
    parser = MessageParser()

    original = {
        "message_type": "CHAT_MESSAGE",
        "sender_name": "Roma",
        "content_type": "TEXT",
        "message_text": "Hello world!",
        "sequence_number": 123,
    }

    encoded = parser.encode_message(original)
    print("Encoded message:\n", encoded)

    decoded = parser.decode_message(encoded)
    print("Decoded dict:", decoded)

    assert decoded == {k: str(v) for k, v in original.items()}, "Parser mismatch!"
    print("✅ MessageParser encode/decode OK\n")


# ---------- BATTLESTATE DISCREPANCY TEST ----------

def test_battle_discrepancy():
    print("=== test_battle_discrepancy ===")
    state = BattleState(is_host=True, seed=42, verbose=True)

    my_poke = {"name": "Pika", "hp": 100}
    opp_poke = {"name": "Char", "hp": 100}
    state.set_pokemon_data(my_poke, opp_poke)

    # Fake a turn where we think opponent HP is 60, opponent says 55
    state.sequence_number = 1
    state.local_calculation = {"hp": 60, "sequence": 1}
    state.receive_calculation_report(opponent_hp=55, opponent_seq=1)

    has_disc = state.has_discrepancy()
    print("has_discrepancy() returned:", has_disc)
    assert has_disc is True, "Expected a discrepancy but got none!"

    payload = state.get_resolution_payload()
    print("Resolution payload:", payload)
    assert payload["remaining_health"] == 60
    assert payload["sequence_number"] == 1

    # Apply resolved HP (e.g., peers agree on 60)
    state.apply_resolved_opponent_hp(60)
    print("Opponent HP after resolution:", state.opponent_pokemon["hp"])
    assert state.opponent_pokemon["hp"] == 60

    # Force terminate due to mismatch (simulate failure to agree)
    state.force_terminate_due_to_mismatch()
    from game.battle_state import GamePhase  # adjust if your enum file is named differently
    assert state.current_phase == GamePhase.GAME_OVER
    print("✅ BattleState discrepancy helpers OK\n")


# ---------- CHATHANDLER TEST (TEXT + STICKER SAVE) ----------

class DummySocket:
    """Fake socket that just prints what is sent instead of really sending."""
    def sendto(self, data: bytes, addr):
        print(f"[DummySocket] Would send to {addr}: {data.decode()[:80]}...")


def test_chat_handler():
    print("=== test_chat_handler ===")
    dummy_socket = DummySocket()
    parser = MessageParser()

    # No ReliableUDP here, we just test handle_incoming + sticker save.
    chat = ChatHandler(
        socket_obj=dummy_socket,
        my_name="Roma",
        peer_addr=("127.0.0.1", 9999),
        reliable=None,
        verbose=True,
        sticker_dir="test_stickers",
    )

    # Simulate receiving a TEXT chat message
    incoming_text = {
        "message_type": "CHAT_MESSAGE",
        "sender_name": "Teammate",
        "content_type": "TEXT",
        "message_text": "Hi Roma!",
    }
    print("Simulating incoming text message...")
    chat.handle_incoming(incoming_text)

    # Simulate receiving a STICKER chat message
    fake_image_bytes = b"this-is-not-a-real-image-but-thats-okay"
    b64_data = base64.b64encode(fake_image_bytes).decode()

    incoming_sticker = {
        "message_type": "CHAT_MESSAGE",
        "sender_name": "Teammate",
        "content_type": "STICKER",
        "sticker_data": b64_data,
    }
    print("Simulating incoming sticker message...")
    chat.handle_incoming(incoming_sticker)

    # Check that a file was created in test_stickers/
    files = os.listdir("test_stickers")
    print("Sticker files:", files)
    assert len(files) > 0, "No sticker file was saved!"
    print("✅ ChatHandler text + sticker saving OK\n")


# ---------- RELIABLEUDP HELPER TEST ----------

class DummySockRU:
    """Dummy socket for ReliableUDP helper tests (no real network)."""
    def __init__(self):
        self._timeout = None

    def gettimeout(self):
        return self._timeout

    def settimeout(self, t):
        self._timeout = t

    def sendto(self, data: bytes, addr):
        print(f"[DummySockRU] sendto called to {addr}: {data.decode()[:80]}...")

    def recvfrom(self, bufsize: int):
        # Always timeout by raising socket.timeout
        import socket
        raise socket.timeout()


def test_reliableudp_helpers():
    print("=== test_reliableudp_helpers ===")
    import socket

    sock = DummySockRU()
    ru = ReliableUDP(sock, timeout=0.1, max_retries=2, verbose=True, loss_prob=0.0)

    # Sequence number generation
    s1 = ru.next_sequence()
    s2 = ru.next_sequence()
    print("Generated sequence numbers:", s1, s2)
    assert s2 == s1 + 1

    # Duplicate detection
    msg1 = {"sequence_number": s1}
    msg2 = {"sequence_number": s1}
    first = ru.is_duplicate(msg1)  # should be False
    second = ru.is_duplicate(msg2) # should be True

    print("Duplicate test -> first:", first, " second:", second)
    assert first is False
    assert second is True

    # Try send_reliable (it will timeout and return False because DummySockRU never ACKs)
    data = {"message_type": "TEST_MSG"}
    ok = ru.send_reliable(data, ("127.0.0.1", 9999))
    print("send_reliable() returned:", ok)
    assert ok is False  # expected: no ACK

    print("✅ ReliableUDP helpers OK (sequence, duplicates, retries)\n")


# ---------- MAIN ----------

if __name__ == "__main__":
    # run tests
    test_message_parser()
    test_battle_discrepancy()
    test_chat_handler()
    test_reliableudp_helpers()
    print("🎉 All sandbox tests completed without assertion errors.")
