# assets-parser.py

Parse Diabotical `.assets` files

Recursively parses all `.assets` files in a given directory and converts everything into a single JSON file. There's a lot of syntax errors inside `.assets` files and while this script handles all of those, in some cases the parser will probably handle things differently than the games parser.


## Usage

```
python3 asset-parser.py src_directory dest_directory
```