# dbp-packer.py

Pack/unpack Diabotical .dbp files

## Usage

```
python3 dbp-pack.py list <file.dbp>
python3 dbp-pack.py unpack <file.dbp>
python3 dbp-pack.py pack <src-folder> <out.dbp>
```

## File format

```
> Header
4 byte header (DBP1)
4 byte version
4 byte number of file index items (uint32)

> File index items
4 bytes filename length (uint32)
N bytes filename (ASCII, not sure about unicode support)
4 bytes offset (uint32)
4 bytes length (uint32)

The offset in the file index item is from the end of the file index itself rather than the beginning of the file.

> Files itself
Files are not compressed or encrypted so to extract one just read SIZE bytes from end-of-index + OFFSET
```

## Credits

Thanks to [@derrod](https://github.com/derrod) for helping with this.