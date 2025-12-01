# networking/udp.py
"""
UDP helper + very simple reliability layer.
"""

import socket
import time
from typing import Tuple

from networking.message_parser import MessageParser


class ReliableUDP:
    """
    Very small reliability wrapper on top of a UDP socket.

    - Adds ACK / ack_number messages
    - Retransmits if ACK not received within timeout
    - Not automatically used by host/joiner yet; but
      ready to be hooked in.
    """

    def __init__(
        self,
        sock: socket.socket,
        timeout: float = 0.5,
        max_retries: int = 3,
        verbose: bool = False,
    ) -> None:
        self.sock = sock
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose
        self.parser = MessageParser()

    def log(self, *args):
        if self.verbose:
            print("[ReliableUDP]", *args)

    def _is_ack_for(self, msg: dict, seq_no: int) -> bool:
        return (
            msg.get("message_type") == "ACK"
            and str(msg.get("ack_number")) == str(seq_no)
        )

    def send_ack(self, addr: Tuple[str, int], seq_no: int) -> None:
        """Send a simple ACK for a given sequence number."""
        ack_msg = {
            "message_type": "ACK",
            "ack_number": seq_no,
        }
        raw = self.parser.encode_message(ack_msg)
        self.sock.sendto(raw.encode(), addr)
        self.log("Sent ACK for", seq_no, "to", addr)

    def send_reliable(self, data: dict, addr: Tuple[str, int]) -> bool:
        """
        Send a message and wait for an ACK.
        Expects 'sequence_number' to already be set in `data`.

        Returns True if ACK received, False otherwise.
        """
        if "sequence_number" not in data:
            # Can't do reliability without a sequence number.
            # Just fire-and-forget.
            raw = self.parser.encode_message(data)
            self.sock.sendto(raw.encode(), addr)
            self.log("Sent NON-RELIABLE message (no sequence_number).")
            return True

        seq_no = data["sequence_number"]
        raw = self.parser.encode_message(data)

        old_timeout = self.sock.gettimeout()
        self.sock.settimeout(self.timeout)

        try:
            for attempt in range(1, self.max_retries + 1):
                self.log(f"Sending seq={seq_no}, attempt={attempt}")
                self.sock.sendto(raw.encode(), addr)

                try:
                    while True:
                        packet, from_addr = self.sock.recvfrom(4096)
                        msg = self.parser.decode_message(packet.decode())

                        # If it's an ACK for us, done!
                        if self._is_ack_for(msg, seq_no):
                            self.log(f"ACK received for seq={seq_no}")
                            return True

                        # If it's some other message, the main
                        # host/joiner code can handle it separately.
                        self.log("Received non-ACK while waiting:", msg)

                except socket.timeout:
                    # Timeout → retransmit
                    self.log("Timeout waiting for ACK for seq", seq_no)
                    continue

            self.log(f"Giving up on seq={seq_no} after {self.max_retries} retries.")
            return False

        finally:
            # restore original timeout (maybe None)
            self.sock.settimeout(old_timeout)
