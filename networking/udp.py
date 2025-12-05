# networking/udp.py

import random
import socket
import time
from typing import Dict, Any
from chat.verbose_mode import VerboseManager


class ReliableUDP:
    """
    A very simple reliability wrapper on top of UDP.

    - Adds a "sequence_number" field to outgoing messages.
    - Retries sending the same datagram up to max_retries.
    - Waits for a JSON-encoded ACK:
        { "message_type": "ACK", "sequence_number": <seq> }

    NOTE: This class does NOT automatically send ACKs.
    Your application code (host/joiner/spectator/protocols) must:
        - Look for incoming messages with a "sequence_number".
        - For non-ACK messages, send back an ACK using the same seq.
    """

    def __init__(
        self,
        socket_obj: socket.socket,
        parser,
        timeout: float = 0.5,
        max_retries: int = 3,
        loss_prob: float = 0.0,
        verbose: bool = False,
    ):
        self.sock = socket_obj
        self.parser = parser
        self.timeout = timeout
        self.max_retries = max_retries
        self.loss_prob = loss_prob
        self._next_seq = 0
        self._received_seqs = set()  # Track received sequence numbers for duplicate detection

    def log(self, *args):
        if VerboseManager.is_verbose():
            print("[ReliableUDP]", *args)

    def next_sequence_number(self) -> int:
        self._next_seq += 1
        self.log("Next sequence number:", self._next_seq)
        return self._next_seq

    def _is_ack_for(self, msg_dict: Dict[str, Any], seq: int) -> bool:
        if msg_dict.get("message_type") != "ACK":
            return False
        return int(msg_dict.get("sequence_number", -1)) == seq

    def send_reliable(self, message_dict: Dict[str, Any], addr) -> bool:
        """
        Encode message_dict as JSON, add sequence_number, send, and wait for ACK.

        Returns True if ACK is received, False otherwise.
        """
        seq = self.next_sequence_number()
        message_dict = dict(message_dict)  # copy so we don't mutate caller's dict
        message_dict["sequence_number"] = seq

        payload = self.parser.encode_message(message_dict).encode("utf-8")

        attempt = 0
        while attempt < self.max_retries:
            attempt += 1

            # artificial loss for testing, if desired
            if random.random() < self.loss_prob:
                self.log(f"(Simulated drop) seq={seq}, attempt={attempt}")
            else:
                self.log(f"Sending seq={seq}, attempt={attempt}")
                self.sock.sendto(payload, addr)

            # wait for ack
            self.sock.settimeout(self.timeout)
            try:
                data, _ = self.sock.recvfrom(65535)
            except socket.timeout:
                self.log(f"Timeout waiting for ACK for seq {seq}")
                continue  # retry
            finally:
                self.sock.settimeout(None)

            try:
                msg = self.parser.decode_message(data.decode("utf-8"))
            except Exception as e:
                self.log("Failed to decode potential ACK:", e)
                continue

            if self._is_ack_for(msg, seq):
                self.log(f"Received ACK for seq={seq}")
                return True
            else:
                self.log("Received non-ACK or wrong seq while waiting for ACK:", msg)

        self.log(f"Giving up on seq={seq} after {self.max_retries} retries.")
        return False

    def is_duplicate(self, msg_dict: Dict[str, Any]) -> bool:
        """Check if a message with this sequence number has already been received."""
        if "sequence_number" not in msg_dict:
            return False
        seq = msg_dict.get("sequence_number")
        if seq in self._received_seqs:
            self.log(f"Duplicate message detected: seq={seq}")
            return True
        self._received_seqs.add(seq)
        return False

    def send_ack(self, addr, sequence_number: int) -> bool:
        """Send an ACK message back to the sender."""
        ack_msg = {
            "message_type": "ACK",
            "sequence_number": sequence_number,
        }
        payload = self.parser.encode_message(ack_msg).encode("utf-8")
        try:
            self.sock.sendto(payload, addr)
            self.log(f"Sent ACK for seq={sequence_number}")
            return True
        except Exception as e:
            self.log(f"Failed to send ACK for seq={sequence_number}: {e}")
            return False
