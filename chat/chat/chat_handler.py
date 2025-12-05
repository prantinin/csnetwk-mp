# chat/chat_handler.py

import base64
import os
import time
from typing import Optional, Dict, Any


class ChatHandler:
    """
    Handles sending and receiving chat messages (plain text or stickers)
    over a ReliableUDP wrapper.

    Message format (all go through ReliableUDP.send_reliable):

    TEXT:
        {
            "message_type": "CHAT_MESSAGE",
            "sender_name": "HOST" / "JOINER" / "SPECTATOR",
            "content_type": "TEXT",
            "message_text": "hello"
        }

    SIMPLE STICKER (emoji / name only, no file):
        {
            "message_type": "CHAT_MESSAGE",
            "sender_name": "...",
            "content_type": "STICKER",
            "sticker_name": "heart"
        }

    STICKER_FILE (base64-encoded image):
        {
            "message_type": "CHAT_MESSAGE",
            "sender_name": "...",
            "content_type": "STICKER_FILE",
            "sticker_name": "heart",
            "sticker_data_b64": "<base64 bytes>"
        }
    """

    def __init__(
        self,
        socket_obj,
        my_name: str,
        peer_addr,
        reliable,
        verbose: bool = True,
    ):
        self.sock = socket_obj
        self.my_name = my_name
        self.peer_addr = peer_addr  # (ip, port)
        self.reliable = reliable    # networking.udp.ReliableUDP
        self.verbose = verbose

        # where to save received sticker files
        self.sticker_dir = "stickers_received"
        os.makedirs(self.sticker_dir, exist_ok=True)

    # ---------- logging helper ----------

    def log(self, *args):
        if self.verbose:
            print("[CHAT]", *args)

    # ---------- low-level send via ReliableUDP ----------

    def _send_raw(self, msg_dict: Dict[str, Any]) -> bool:
        """
        Sends a dict via ReliableUDP. Returns True if ACKed, False otherwise.
        ReliableUDP will add sequence_number automatically.
        """
        self.log("Outgoing chat:", msg_dict)
        ok = self.reliable.send_reliable(msg_dict, self.peer_addr)
        if not ok:
            self.log("reliable send failed (no ACK).")
        return ok

    # ---------- public send helpers ----------

    def send_text(self, text: str) -> None:
        """
        Send a plain text chat message.
        """
        msg = {
            "message_type": "CHAT_MESSAGE",
            "sender_name": self.my_name,
            "content_type": "TEXT",
            "message_text": text,
        }
        self._send_raw(msg)
        self.log("Sent text:", text)

    def send_sticker(self, sticker_name: str) -> None:
        """
        Send a simple named sticker (no file, just the name).
        E.g. /sticker heart
        """
        msg = {
            "message_type": "CHAT_MESSAGE",
            "sender_name": self.my_name,
            "content_type": "STICKER",
            "sticker_name": sticker_name,
        }
        self._send_raw(msg)
        self.log("Sent sticker:", sticker_name)

    def send_sticker_from_file(self, filepath: str, sticker_name: Optional[str] = None) -> None:
        """
        Load a file (e.g. PNG / JPG), base64-encode it, and send as STICKER_FILE.

        Usage from the game:
            /stickerfile path/to/image.png
            /stickerfile path/to/image.png custom_name
        """
        if not os.path.isfile(filepath):
            self.log("Sticker file does not exist:", filepath)
            return

        try:
            with open(filepath, "rb") as f:
                data = f.read()
        except Exception as e:
            self.log("Failed to read sticker file:", e)
            return

        b64 = base64.b64encode(data).decode("ascii")
        if sticker_name is None:
            sticker_name = os.path.basename(filepath)

        msg = {
            "message_type": "CHAT_MESSAGE",
            "sender_name": self.my_name,
            "content_type": "STICKER_FILE",
            "sticker_name": sticker_name,
            "sticker_data_b64": b64,
        }
        self._send_raw(msg)
        self.log("Sent sticker file:", sticker_name, f"({len(b64)} base64 chars)")

    # ---------- incoming messages ----------

    def handle_incoming(self, msg: Dict[str, Any]) -> None:
        """
        Handle an incoming CHAT_MESSAGE dict.
        This is called by Protocols.recv_non_chat(), host, joiner, spectator, etc.
        """
        sender = msg.get("sender_name", "Unknown")
        content_type = msg.get("content_type", "TEXT")

        if content_type == "TEXT":
            text = msg.get("message_text", "")
            print(f"[CHAT] {sender}: {text}")

        elif content_type == "STICKER":
            name = msg.get("sticker_name", "sticker")
            print(f"[CHAT] {sender} sent sticker: [{name}]")

        elif content_type == "STICKER_FILE":
            b64_data = msg.get("sticker_data_b64", "")
            name = msg.get("sticker_name", "sticker")
            filename = self._save_sticker_file(b64_data, sender, name)
            if filename:
                print(f"[CHAT] {sender} sent sticker file '{name}' → saved as {filename}")
            else:
                print(f"[CHAT] {sender} sent sticker file '{name}' (failed to save).")

        else:
            print(f"[CHAT] {sender} sent unknown content_type={content_type}: {msg}")

    # ---------- helper: save sticker files ----------

    def _save_sticker_file(self, b64_data: str, sender: str, sticker_name: str) -> Optional[str]:
        """
        Decode base64 and save to a file in stickers_received/.
        """
        if not b64_data:
            return None

        try:
            binary = base64.b64decode(b64_data)
        except Exception as e:
            self.log("Failed to base64-decode sticker:", e)
            return None

        ts = int(time.time())
        safe_name = sticker_name.replace("/", "_").replace("\\", "_")
        filename = f"{sender}_{safe_name}_{ts}.bin"
        path = os.path.join(self.sticker_dir, filename)

        try:
            with open(path, "wb") as f:
                f.write(binary)
            self.log("Saved sticker to", path)
            return path
        except Exception as e:
            self.log("Failed to write sticker file:", e)
            return None
