# Diabotical tools

A collection of python CLI tools I created or extended that do stuff with Diabotical game files:

* [dbp-packer.py](dbp-packer.md): Pack/unpack Diabotical `.dbp` files
* [assets-parser.py](assets-parser.md): Parse Diabotical `.assets` files
* [rbe-parser.py](rbe-parser.md): Parse Diabotical `.rbe` map files and create minimap images

While I tried to make this Windows-compatible, I haven't tested it. Try using WSL if things don't work.

Example usage:

* Copy all `.dbp` files from the game into the `_packs` folder
* Use `./unpack_all.sh` to unpack everything to `_unpacked`
* Create a minimap: `python3 rbe-parser.py _unpacked/maps/wo_wellspring.rbe --minimap`
* Create assets JSON: `./assets-parser.py _unpacked .`

## More?

I have a few more tools that I might release at some point.

### Masterserver Tool

Emulates a masterserver that a real game client can connect and talk to or emulate a client and talk to the real masterserver to programmatically carry out actions (for example querying the server browser or creating lobbies).

It is currently in use on https://diabotical.cool/servers

Challenges: While the tool is mostly complete, authentication is not straight forward and at the moment requires manual usage of external tools. I'm also not comfortable releasing this publicly as there is potential to mess with in-production game systems.


### Netcode PoC

The games netcode is based on Raknet. I wrote something that can talk Raknet, connect to game servers and understand some of the Diabotical specific packets. There's a lot of custom packets, so this isn't complete in any way. But the general framework is there, with which it is possible to connect to a game server and chat with real clients.

Challenges: It's a lot of trial and error to manually decode all packets plus there's a lot of complexity to make this into a program that can actually do something with the protocol. I'm not going to put this out at this time, as there's cheating potential here.