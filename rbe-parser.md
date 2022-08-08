# rbe-parser.py

Parse Diabotical .rbe map files

* This is an adaptation of https://github.com/Press-OK/ParseRBE with a few additions.
* Writing map files is possible, but the implementation is not maintained and it's likely broken.
* Optionally outputs the parsed map data to JSON, which is just for demonstration and not really super useful. Caution: the JSON file will be huge.
* Optionally creates a minimap image. This requires an external dependency: `pip3 install -r requirements.txt`

## Usage

```
python3 rbe-parser.py [--json] [--minimap] <wo_wellspring.rbe>
```

## Additions compared to ParseRBE

* Compatibility with recent game version (map file version `26`, Diabotical game version `0.20.468`)
* Unpacks gzipped map structure
* Fixed a few inaccuracies
* Added the ability to translate the minimap data into an image
* Added a CLI interface

There's a unknown prop structure at the end of the file that was added to the map format some point. This isn't being parsed yet.

## Credits

* Most of the original reverse-engineering was done by Armaku (Discord)
* ParseRBE script originally written by PressOK (twitch.tv/PressOK)