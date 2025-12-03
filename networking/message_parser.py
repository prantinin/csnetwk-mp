import json

class MessageParser:

    # Encoding message from dictionary to string
    def encode_message(self, data: dict) -> str:
        return json.dumps(data)


    # Decoding message from string to dictionary
    def decode_message(self, message: str) -> dict:
        return json.loads(message)