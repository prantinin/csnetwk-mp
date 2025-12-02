# networking/udp.py
"""
UDP helper + reliability layer.

Covers:
- Sequence numbers
- ACK messages
- Retransmission with timeout + retry count
- Optional simulated packet loss
- Duplicate detection helper
"""

import socket
import time
import random
from typing import Tuple, Dict, Set

from networking.message_parser import MessageParser


class ReliableUDP:
    def __init__(
        self,
        sock: socket.socket,
        timeout: float = 0.5,
        max_retries: int = 3,
        verbose: bool = False,
        loss_prob: float = 0.0,  # 0.0 = no simulated loss
    ) -> None:
        self.sock = sock
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose
        self.parser = MessageParser()
        self.loss_prob = loss_prob

        self._next_seq = 1  # internal sequence counter
        self._seen_sequences: Set[int] = set()  # for duplicate handling

    # --- logging ---

    def log(self, *args):
        if self.verbose:
            print("[ReliableUDP]", *args)

    # --- sequence helper ---

    def next_sequence(self) -> int:
        seq = self._next_seq
        self._next_seq += 1
        self.log("Next sequence number:", seq)
        return seq

    # --- ACK helpers ---

    def _is_ack_for(self, msg: dict, seq_no: int) -> bool:
        return (
            msg.get("message_type") == "ACK"
            and str(msg.get("ack_number")) == str(seq_no)
        )

    def send_ack(self, addr: Tuple[str, int], seq_no: int) -> None:
        """Send a simple ACK for a given sequence number (fire-and-forget)."""
        ack_msg = {
            "message_type": "ACK",
            "ack_number": seq_no,
        }
        raw = self.parser.encode_message(ack_msg)

        # Optional simulated loss
        if self.loss_prob > 0 and random.random() < self.loss_prob:
            self.log(f"[LOSS] Simulating lost ACK for seq={seq_no}")
            return

        self.sock.sendto(raw.encode(), addr)
        self.log("Sent ACK for", seq_no, "to", addr)

    # --- duplicate detection helper ---

    def is_duplicate(self, msg: dict) -> bool:
        """
        Returns True if we've already seen this sequence_number before.
        Use this in host/joiner to ignore repeated packets.
        """
        try:
            seq = int(msg.get("sequence_number"))
        except (TypeError, ValueError):
            return False  # no valid seq number, can't judge

        if seq in self._seen_sequences:
            self.log("Duplicate received for seq", seq)
            return True

        self._seen_sequences.add(seq)
        return False

    # --- main reliable send ---

    def send_reliable(self, data: dict, addr: Tuple[str, int]) -> bool:
        """
        Send a message and wait for an ACK.

        REQUIREMENT: data must contain 'sequence_number'.
        Returns True if ACK received, False if retries exhausted.
        """
        if "sequence_number" not in data:
            # If user forgot, assign one automatically
            data["sequence_number"] = self.next_sequence()

        seq_no = data["sequence_number"]
        raw = self.parser.encode_message(data)

        old_timeout = self.sock.gettimeout()
        self.sock.settimeout(self.timeout)

        try:
            for attempt in range(1, self.max_retries + 1):
                # Simulated loss: pretend to send but drop some packets
                if self.loss_prob > 0 and random.random() < self.loss_prob:
                    self.log(
                        f"[LOSS] Simulating lost send for seq={seq_no}, attempt={attempt}"
                    )
                else:
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

                        # If it's some other message, main app should handle it.
                        # Here we just log it for debug.
                        self.log("Received non-ACK while waiting:", msg)

                except socket.timeout:
                    # Timeout → retransmit
                    self.log("Timeout waiting for ACK for seq", seq_no)
                    continue

            self.log(f"Giving up on seq={seq_no} after {self.max_retries} retries.")
            return False

        finally:
            self.sock.settimeout(old_timeout)
