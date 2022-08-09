# demo-parser

Parse meta information of demo files

Can parse local demo files and server demos and writes JSON to `stdout` or a file.

Without analyzing it too deeply, it looks like the file format is more or less a recording of the network packets between client and server. Currently, this tool parses the demos header and looks for two specific "packets" that have a JSON payload and outputs the content of those into the following properties of the resulting JSON:

* `start_json`: Basic information (game mode, server ip, etc.) and information on the players that are now connecting to the server (or for local demos: information on the players that were present on the server when the recording player connected)
* `end_json`: Basic information, match results (team and player stats) when the match ended (for local demos, this property might not be present if the recording player disconnected)

## Usage

```
python3 demo-parser.py [--json] demo_file [demo_file ...]
```