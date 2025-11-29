# csnetwk-mp
Peer-to-Peer Pokémon Battle Protocol (PokeProtocol) using UDP as its transport layer, with an added feature for peer-to-peer text chat that now includes an option for sending stickers.

## How to Run
1. Open a terminal to the project directory and run the host file using this command  
    `python -m pokeprotocol.host`
2. You can run the joiner and spectator files by opening separate terminals and using one of these commands  
    `python -m pokeprotocol.joiner`  
    `python -m pokeprotocol.spectator`

## Resources
- https://realpython.com/python-sockets/#echo-client-and-server
- https://stackoverflow.com/questions/3939361 remove-specific-characters-from-a-string-in-python 

## Generative AI Statement
We acknowledge the use of ChatGPT and CoPilot in the development of this application. We have understood its purpose and assessed its correctness within the entirety of the code. The prompts used are listed below and the output from these prompts were used for the following causes:
- Understanding how the application's output would look like
- Knowing how to implement socket programming concepts
- Checking for errors and their fixes

## Prompts Used in Generative AI 
- How would the general flow of this application look like?
- Differences in TCP and UDP socket programming
- How to make UDP handshake protocol python
- How to parse messages in python
- Error checking (e.g. why am I getting this error)