class MessageParser:

    # Encoding message from dictionary to string
    def encode_message(self, data: dict) -> str:
        return "\n".join([f"{key}: {value}" for key, value in data.items()])


    # Decoding message from string to dictionary
    def decode_message(self, message: str) -> dict:
        parsed_data = {}
        for line in message.split("\n"):
            key, value = line.split(": ", 1)
            parsed_data[key] = value
        return parsed_data