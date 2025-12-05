from __future__ import annotations

from typing import Optional
import socket

from chat.chat_handler import ChatHandler
from networking.message_parser import MessageParser
from game.battle_state import BattleState
from game.pokemon_stats import load_pokemon_stats, get_by_name

parser = MessageParser()

your_turn_divider = "================== YOUR TURN ==============\n"
their_turn_divider = "================== OPPONENT'S TURN =======\n"


class Protocols:
    def __init__(self):
        self.pokemon_stats = load_pokemon_stats("game/pokemon.csv")
        self.chat_handler: Optional[ChatHandler] = None

    # ------------------------------------------------------------------
    # CHAT-HANDLER ATTACH
    # ------------------------------------------------------------------
    def attach_chat_handler(self, handler: ChatHandler):
        self.chat_handler = handler

    # ------------------------------------------------------------------
    # CHAT COMMANDS
    # ------------------------------------------------------------------
    def maybe_handle_chat_command(self, text: str) -> bool:
        """Intercept /chat, /sticker, /stickerfile commands."""
        if not text.startswith("/"):
            return False

        if not self.chat_handler:
            print("[CHAT] (no chat handler attached)")
            return True

        # /chat message
        if text.startswith("/chat "):
            msg = text[len("/chat "):].strip()
            if msg:
                self.chat_handler.send_text(msg)
            else:
                print("[CHAT] Usage: /chat <message>")
            return True

        # /sticker name
        if text.startswith("/sticker "):
            name = text[len("/sticker "):].strip()
            if name:
                self.chat_handler.send_sticker(name)
            else:
                print("[CHAT] Usage: /sticker <name>")
            return True

        # /stickerfile path [label]
        if text.startswith("/stickerfile "):
            parts = text.split(maxsplit=2)
            if len(parts) < 2:
                print("[CHAT] Usage: /stickerfile <path> [label]")
                return True

            path = parts[1]
            label = parts[2] if len(parts) == 3 else None
            self.chat_handler.send_sticker_from_file(path, label)
            return True

        print("[CHAT] Unknown command.")
        return True

    # ------------------------------------------------------------------
    # INPUT WRAPPER
    # ------------------------------------------------------------------
    def input_with_chat(self, prompt: str) -> str:
        while True:
            user_input = input(prompt).strip()
            if user_input.startswith("/"):
                self.maybe_handle_chat_command(user_input)
                continue
            return user_input

    # ------------------------------------------------------------------
    # RECV FILTER
    # ------------------------------------------------------------------
    def recv_non_chat(self, sock: socket.socket, bufsize=4096):
        """Filter CHAT_MESSAGE from battle logic."""
        while True:
            data, addr = sock.recvfrom(bufsize)
            msg = parser.decode_message(data.decode())

            if msg.get("message_type") == "CHAT_MESSAGE":
                if self.chat_handler:
                    self.chat_handler.handle_incoming(msg)
                continue

            return msg, addr

    # ------------------------------------------------------------------
    # BATTLE SETUP: HOST
    # ------------------------------------------------------------------
    def host_battle_setup(self):
        health = 100

        # comms
        while True:
            comms = self.input_with_chat("What communication mode would you like? (P2P/BROADCAST) ")
            comms = comms.upper()
            if comms in ("P2P", "BROADCAST"):
                break
            print("Please choose only P2P or BROADCAST.\n")

        # pokemon
        while True:
            poke_name = self.input_with_chat("Choose your Pokemon: ").lower()
            poke = get_by_name(poke_name, self.pokemon_stats)
            if poke is None:
                print("Pokemon not found in CSV.")
                continue
            print(poke)
            mypoke = {"pokemon": poke_name, "hp": health}
            break

        atk = self.input_with_chat("How much special attack boost? ")
        df = self.input_with_chat("How much special defense boost? ")

        return {
            "communication_mode": comms,
            "pokemon_name": mypoke,
            "stat_boosts": {
                "special_attack_uses": atk,
                "special_defense_uses": df,
            }
        }

    # ------------------------------------------------------------------
    # BATTLE SETUP: JOINER
    # ------------------------------------------------------------------
    def joiner_battle_setup(self):
        health = 140

        poke_name = self.input_with_chat("Choose your Pokemon: ").lower()
        atk = self.input_with_chat("How much special attack boost? ")
        df = self.input_with_chat("How much special defense boost? ")

        return {
            "pokemon_name": {"pokemon": poke_name, "hp": health},
            "stat_boosts": {
                "special_attack_uses": atk,
                "special_defense_uses": df,
            }
        }

    # ------------------------------------------------------------------
    # MAIN TURN: ATTACK
    # ------------------------------------------------------------------
    def your_turn(self, sock, addr, state: BattleState):
        print(your_turn_divider)

        move = self.input_with_chat("Choose your attack move: ").lower()

        attack_msg = {
            "message_type": "ATTACK_ANNOUNCE",
            "move_name": {"move": move, "move_damage": 20},
            "sequence_number": state.next_sequence_number(),
        }

        state.record_attack_announce(attack_msg["move_name"])
        sock.sendto(parser.encode_message(attack_msg).encode(), addr)
        print("Attack announced.\n")

        # wait for DEFENSE_ANNOUNCE
        msg, _ = self.recv_non_chat(sock)
        if msg.get("message_type") != "DEFENSE_ANNOUNCE":
            print("Unexpected:", msg)
            return

        state.receive_defense_announce()

        # damage
        remaining = state.opponent_pokemon["hp"] - state.last_attack["move_damage"]
        state.opponent_pokemon["hp"] = remaining

        calc_msg = {
            "message_type": "CALCULATION_REPORT",
            "attacker": state.my_pokemon["pokemon"],
            "move_used": move,
            "remaining_health": state.my_pokemon["hp"],
            "damage_dealt": 20,
            "defender_hp_remaining": remaining,
            "status_message": f"{move} dealt 20 damage!",
            "sequence_number": state.next_sequence_number(),
        }

        state.send_calculation_confirm()
        sock.sendto(parser.encode_message(calc_msg).encode(), addr)

        # wait opponent calc
        msg, _ = self.recv_non_chat(sock)
        state.receive_calculation_confirm()

        # switch turn
        if state.both_confirmed():
            confirm = {
                "message_type": "CALCULATION_CONFIRMATION",
                "sequence_number": state.next_sequence_number(),
            }
            sock.sendto(parser.encode_message(confirm).encode(), addr)
            state.switch_turn()

    # ------------------------------------------------------------------
    # OPPONENT TURN
    # ------------------------------------------------------------------
    def their_turn(self, sock, addr, state: BattleState):
        print(their_turn_divider)
        print("Waiting for opponent's move...\n")

        msg, _ = self.recv_non_chat(sock)
        state.receive_attack_announce(msg["move_name"])

        def_msg = {
            "message_type": "DEFENSE_ANNOUNCE",
            "sequence_number": state.next_sequence_number()
        }
        sock.sendto(parser.encode_message(def_msg).encode(), addr)
        state.receive_defense_announce()

        # opponent calc
        msg, _ = self.recv_non_chat(sock)
        state.receive_calculation_confirm()
        state.receive_calculation_report(
            msg["defender_hp_remaining"],
            msg["sequence_number"],
        )

        # our calc
        remaining = state.my_pokemon["hp"] - state.last_attack["move_damage"]
        state.my_pokemon["hp"] = remaining

        calc_msg = {
            "message_type": "CALCULATION_REPORT",
            "attacker": state.opponent_pokemon["pokemon"],
            "move_used": state.last_attack["move"],
            "remaining_health": state.opponent_pokemon["hp"],
            "damage_dealt": state.last_attack["move_damage"],
            "defender_hp_remaining": remaining,
            "status_message": "Damage processed",
            "sequence_number": state.next_sequence_number(),
        }

        sock.sendto(parser.encode_message(calc_msg).encode(), addr)
        state.send_calculation_confirm()
        state.record_local_calculation(remaining)

        # wait confirm
        msg, _ = self.recv_non_chat(sock)

        if msg.get("message_type") == "CALCULATION_CONFIRMATION":
            if state.both_confirmed():
                state.switch_turn()

    # ------------------------------------------------------------------
    # GAME LOOP
    # ------------------------------------------------------------------
    def start_game(self, sock, addr, state: BattleState):
        while not state.check_game_over():
            if state.my_turn:
                self.your_turn(sock, addr, state)
            else:
                self.their_turn(sock, addr, state)

        print("\n\n===== GAME OVER =====\n\n")
