# chat/chat_handler.py

import base64
import os
from datetime import datetime

from typing import Optional

from networking.message_parser import MessageParser
from networking.udp import ReliableUDP


class ChatHandler:
    """
    Simple text/sticker chat helper.

    - If you pass a ReliableUDP instance, messages are sent with ACKs +
      retransmission using sequence_number.
    - If you pass only a raw socket, it will just send via sendto (no ACK).
    """

    def __init__(
        self,
        socket_obj,
        my_name: str,
        peer_addr,
        reliable: Optional[ReliableUDP] = None,
        verbose: bool = False,
        sticker_dir: str = "stickers",
    ):
        self.socket = socket_obj
        self.peer_addr = peer_addr          # (ip, port)
        self.my_name = my_name
        self.verbose = verbose
        self.parser = MessageParser()
        self.reliable = reliable            # may be None
        self.sticker_dir = sticker_dir
        os.makedirs(self.sticker_dir, exist_ok=True)

    def log(self, *args):
        if self.verbose:
            print("[CHAT]", *args)

    # === internal send helpers ===

    def _send_raw(self, msg_dict: dict):
        """
        Send a message either through ReliableUDP (with ACKs) or
        directly via socket.sendto.
        """
        if self.reliable is not None:
            # Ensure a sequence_number exists for reliability
            if "sequence_number" not in msg_dict:
                # If ReliableUDP is used together with BattleState,
                # you can set sequence_number there. For now we just
                # increment internal counter on ReliableUDP.
                msg_dict["sequence_number"] = self.reliable.next_sequence()
            ok = self.reliable.send_reliable(msg_dict, self.peer_addr)
            self.log("Sent reliable chat message, acked:", ok)
        else:
            raw = self.parser.encode_message(msg_dict)
            self.socket.sendto(raw.encode(), self.peer_addr)
            self.log("Sent NON-reliable chat message.")

    # === SENDING ===

    def send_text(self, text: str):
        """Send a plain text chat message (with ACK if ReliableUDP is set)."""
        msg = {
            "message_type": "CHAT_MESSAGE",
            "sender_name": self.my_name,
            "content_type": "TEXT",
            "message_text": text,
        }
        self._send_raw(msg)
        self.log("Sent text:", text)

    def send_sticker(self, sticker_b64: str):
        """
        Send a sticker (Base64-encoded data).
        """
        msg = {
            "message_type": "CHAT_MESSAGE",
            "sender_name": self.my_name,
            "content_type": "STICKER",
            "sticker_data": sticker_b64,
        }
        self._send_raw(msg)
        self.log("Sent sticker (len =", len(sticker_b64), ")")

    # === RECEIVING ===

    def handle_incoming(self, msg: dict):
        """
        Call this from host/joiner when you receive a message
        and message_type == 'CHAT_MESSAGE'.
        """
        if msg.get("message_type") != "CHAT_MESSAGE":
            return  # not for us

        sender = msg.get("sender_name", "Unknown")
        content_type = msg.get("content_type", "TEXT")

        if content_type == "TEXT":
            text = msg.get("message_text", "")
            print(f"[CHAT] {sender}: {text}")

        elif content_type == "STICKER":
            b64_data = msg.get("sticker_data", "")
            filename = self._save_sticker_file(b64_data, sender)
            if filename:
                print(f"[CHAT] {sender} sent a sticker → saved as {filename}")
            else:
                print(f"[CHAT] {sender} sent a sticker (failed to save).")

        else:
            self.log("Unknown chat content_type:", content_type)

    def _save_sticker_file(self, b64_data: str, sender: str) -> Optional[str]:
        """
        Decode base64 sticker data and save it as a PNG file.
        Returns the filename or None on failure.
        """
        if not b64_data:
            self.log("Sticker has no data; skipping save.")
            return None

        try:
            binary = base64.b64decode(b64_data)
        except Exception as e:
            self.log("Failed to decode sticker base64:", e)
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_sender = "".join(c for c in sender if c.isalnum() or c in ("-", "_"))
        filename = f"{safe_sender}_{timestamp}.png"
        path = os.path.join(self.sticker_dir, filename)

        try:
            with open(path, "wb") as f:
                f.write(binary)
            self.log("Saved sticker to", path)
            return path
        except Exception as e:
            self.log("Failed to write sticker file:", e)
            return None
