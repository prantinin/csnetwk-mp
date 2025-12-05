import json
from chat.verbose_mode import VerboseManager

class MessageParser:

    # Encoding message from dictionary to string
    def encode_message(self, data: dict) -> str:
        result = json.dumps(data)
        if VerboseManager.is_verbose():
            msg_type = data.get("message_type", "UNKNOWN")
            print(f"[MSG_PARSER] Encoded {msg_type}: {len(result)} bytes")
        return result


    # Decoding message from string to dictionary
    def decode_message(self, message: str) -> dict:
        result = json.loads(message)
        if VerboseManager.is_verbose():
            msg_type = result.get("message_type", "UNKNOWN")
            print(f"[MSG_PARSER] Decoded {msg_type}: {len(message)} bytes")
        return result