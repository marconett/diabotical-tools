#!/usr/bin/python3

import struct
import sys
import os
import io
import argparse
from pathlib import Path, PureWindowsPath

# > Header
# 4 byte header (DBP1)
# 4 byte unknown (version?)
# 4 byte number of file index items (uint32)

# > File index items
# 4 bytes filename length (uint32)
# N bytes filename (ASCII, not sure about unicode support)
# 4 bytes offset (uint32)
# 4 bytes length (uint32)

# The offset in the file index item is from the end of the file index itself rather than the beginning of the file.

# > Files itself
# Files are not compressed or encrypted so to extract one just read SIZE bytes from end-of-index + OFFSET

class DBPHeader(object):
    magic = b'DBP1'
    unk = b'\x00\x00\x00\x00'

class DBPFile(object):
    def __init__(self):
        self.name_len = 0
        self.name = ''
        self.offset = 0
        self.size = 0

class DBPReader(object):
    def __init__(self):
        self.index = []
        self.num_files = 0
        self.start_offset = 0
        self.file = None

    def read_file(self, dbpf):
        self.file.seek(self.start_offset + dbpf.offset)
        return self.file.read(dbpf.size)

    @classmethod
    def read(cls, file):
        # reads file index and returns class
        dbp = cls()
        dbp.file = file

        magic = file.read(4)
        if magic != DBPHeader.magic:
            raise ValueError('Invalid file!')

        # unknown, but appears to be always zero?
        unk = file.read(4)
        if unk != DBPHeader.unk:
            print("Warning: unexpected unk")

        # number of files
        dbp.num_files = struct.unpack('<I', file.read(4))[0]

        for i in range(dbp.num_files):
            dbpf = DBPFile()
            dbpf.name_len = struct.unpack('<I', file.read(4))[0]
            dbpf.name = file.read(dbpf.name_len).decode('ascii')
            dbpf.offset = struct.unpack('<I', file.read(4))[0]
            dbpf.size = struct.unpack('<I', file.read(4))[0]
            dbp.index.append(dbpf)

        # once all files are read we know the offset from which files are read
        dbp.start_offset = file.tell()
        print(dbp.start_offset)

        return dbp

class DBPWriter(object):
    def __init__(self):
        self.index = []
        self.num_files = 0
        self.start_offset = 0
        self.output_file = None
        self.input_path = None

    @classmethod
    def write(cls, input_path, output_file):
        dbp = cls()
        dbp.output_file = output_file
        dbp.input_path = Path(input_path)

        if dbp.input_path == None:
            raise ValueError('Invalid input path!')

        # write header
        dbp.output_file.write(DBPHeader.magic)
        dbp.output_file.write(DBPHeader.unk)

        # number of files
        for file in dbp.input_path.glob('**/*.*'):
            path = str(file).replace("/", "\\")
            dbp.index.append(path)

        dbp.num_files = struct.pack('<I', len(dbp.index))
        dbp.output_file.write(dbp.num_files)

        # index
        dbp.index = sorted(dbp.index)
        offset = 0
        data = bytearray()

        for file in dbp.index:
            dbpFile = DBPFile()

            local_file = Path(PureWindowsPath(file))

            mf = io.open(local_file, "rb")
            file_content = mf.read()
            data = data + file_content

            size = len(file_content)

            dbpFile.name_len = len(file)
            dbpFile.name = file.encode('ascii')
            dbpFile.offset = offset
            dbpFile.size = size

            offset = offset+size

            dbp.output_file.write(struct.pack('<I', dbpFile.name_len))
            dbp.output_file.write(dbpFile.name)
            dbp.output_file.write(struct.pack('<I', dbpFile.offset))
            dbp.output_file.write(struct.pack('<I', dbpFile.size))

        # data
        dbp.output_file.write(data)
        dbp.output_file.close()


def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='dbp-packer.py', description='.dbp file packer/unpacker for Diabotical')
    parser.add_argument('mode', action='store_true')
    subparsers = parser.add_subparsers(dest="command")

    parser_list = subparsers.add_parser('list', aliases=['l'], help='list the .dbp contents')
    parser_list.add_argument('source', type=argparse.FileType('r'), help="source file")

    parser_unpack = subparsers.add_parser('unpack', aliases=['u'], help='unpack the .dbp file')
    parser_unpack.add_argument('source', type=argparse.FileType('r'), help="source file")
    parser_unpack.add_argument('destination', type=str, help="destination directory")

    parser_pack = subparsers.add_parser('pack', aliases=['p'], help='pack a directory into a .dbp file')
    parser_pack.add_argument('source', type=dir_path, help="source directory")
    parser_pack.add_argument('destination', help="destination file")

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()


    if args.command.startswith("l"):
        # list
        f = io.open(args.source.name, 'rb')
        d = DBPReader.read(f)

        for df in d.index:
            path = Path(PureWindowsPath(df.name))
            print(path)

    elif args.command.startswith("u"):
        # unpack
        path_prefix = Path(PureWindowsPath(args.destination))
        os.makedirs(path_prefix, 0o766, True)

        f = io.open(args.source.name, 'rb')
        d = DBPReader.read(f)

        for df in d.index:
            path = Path(PureWindowsPath(df.name))
            full_path = path_prefix.joinpath(path)
            print(f"{path}\t{df.offset:08x}\t{df.size}")

            os.makedirs(full_path.parents[0], 0o766, True)
            io.open(full_path, "wb").write(d.read_file(df))
        print("DONE")

    elif args.command.startswith("p"):
        # pack
        output_file = io.open(args.destination, "wb")
        w = DBPWriter.write(args.source, output_file)
        print("DONE")