# chat/chat_handler.py

from networking.message_parser import MessageParser


class ChatHandler:
    """
    Simple text/sticker chat helper.

    It does NOT create sockets by itself.
    You pass in the socket + peer address from host/joiner.
    """

    def __init__(self, socket_obj, my_name: str, peer_addr, verbose: bool = False):
        self.socket = socket_obj
        self.peer_addr = peer_addr      # (ip, port) tuple
        self.my_name = my_name
        self.verbose = verbose
        self.parser = MessageParser()

    def log(self, *args):
        if self.verbose:
            print("[CHAT]", *args)

    # === SENDING ===

    def send_text(self, text: str):
        """Send a plain text chat message."""
        msg = {
            "message_type": "CHAT_MESSAGE",
            "sender_name": self.my_name,
            "content_type": "TEXT",
            "message_text": text,
        }
        raw = self.parser.encode_message(msg)
        self.socket.sendto(raw.encode(), self.peer_addr)
        self.log("Sent text:", text)

    def send_sticker(self, sticker_b64: str):
        """
        Send a sticker (Base64-encoded data).
        Right now we just log it; you can extend this later.
        """
        msg = {
            "message_type": "CHAT_MESSAGE",
            "sender_name": self.my_name,
            "content_type": "STICKER",
            "sticker_data": sticker_b64,
        }
        raw = self.parser.encode_message(msg)
        self.socket.sendto(raw.encode(), self.peer_addr)
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
            print(f"[CHAT] {sender} sent a sticker.")
        else:
            self.log("Unknown chat content_type:", content_type)
