#!/usr/bin/python3

import sys
import gzip
import json
import pprint
import re
import io
import argparse
from pathlib import Path
from datetime import datetime

pp = pprint.PrettyPrinter(indent=4, width=10)

class Demo:
  def parse_server_demo_header(self, f):
    self.u1               = decodeInt(f.read(8))

    player_count          = decodeInt(f.read(4))
    self.players          = []
    for i in range(player_count):
        name_len          = decodeInt(f.read(4))
        name              = f.read(name_len).decode("utf-8")
        user_id_len       = decodeInt(f.read(4))
        user_id           = f.read(user_id_len).decode("utf-8")
        p_u1              = decodeInt(f.read(4))
        p_u2              = decodeInt(f.read(4))
        p_u3              = decodeInt(f.read(4))

        p = {
            'name': name,
            'user_id': user_id,
            'p_u1': p_u1,
            'p_u2': p_u2,
            'p_u3': p_u3,
        }
        self.players.append(p)

    reconnect_count       = decodeInt(f.read(4))
    self.reconnects       = []
    for i in range(reconnect_count):
        user_id_len       = decodeInt(f.read(4))
        user_id           = f.read(user_id_len).decode("utf-8")
        r_u1              = decodeInt(f.read(4))
        r_u2              = decodeInt(f.read(4))

        r = {
            'user_id': user_id,
            'r_u1': r_u1,
            'r_u2': r_u2,
        }
        self.reconnects.append(r)


  def parse_client_demo_header(self, f):
    self.created_at       = decodeEpoch(f.read(4))
    padding               = decodeInt(f.read(16))

  def parse(self, f):
    with open(f, 'rb') as f:
        self.format           = f.read(4).decode("utf-8")
        self.format_version   = decodeInt(f.read(4))
        game_version_len      = decodeInt(f.read(4))
        self.game_version     = f.read(game_version_len).decode("utf-8")
        mode_len              = decodeInt(f.read(4))
        self.mode             = f.read(mode_len).decode("utf-8")
        map_len               = decodeInt(f.read(4))
        self.map              = f.read(map_len).decode("utf-8")

        if self.format == 'EVGR':
          self.parse_client_demo_header(f)
        elif self.format == 'DBSR':
          self.parse_server_demo_header(f)
        else:
          print("ERROR: wrong header. not a demo?")
          print(self.format)
          exit(1)


        # as expected, the the gzipped stuff is pretty much just a replay of network packages
        f = io.BytesIO(f.read())
        gf = gzip.GzipFile(fileobj=f)

        packets = gf.read()
        start_packet_header = packets.find(encodeHexString('FF000043 00000000'))
        end_packet_header   = packets.find(encodeHexString('FF00003f 00000000'))

        if start_packet_header > 0:
            gf.seek(start_packet_header, 0)
            start_packet_header = gf.read(8)
            start_json_length = decodeInt(gf.read(4))
            self.start_json = json.loads(gf.read(start_json_length).decode("utf-8"))

        if end_packet_header > 0:
            gf.seek(end_packet_header, 0)
            end_packet_header = gf.read(8)
            end_json_length = decodeInt(gf.read(4))
            self.end_json = json.loads(gf.read(end_json_length).decode("utf-8"))


def encodeInt(data, bytes):
    return data.to_bytes(bytes, "little", signed=True)
def encodeFloat(data):
    return bytearray.fromhex(struct.pack('<f', data).hex())
def encodeString(data):
    return data.encode()
def encodeHexString(hex_string):
    return bytes.fromhex(hex_string)
def decodeInt(data):
    return int.from_bytes(data, "little", signed=True)
def decodeEpoch(data):
    i = int.from_bytes(data, "little", signed=True)
    return datetime.fromtimestamp(i)
def decodeFloat(data):
    return struct.unpack('<f', data)[0]
def degToRad(degrees):
    return degrees * math.pi / 180
def radToDeg(radians):
    return radians * 180 / math.pi

class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(prog='demo-parser.py', description="demo file parser for Diabotical")
  parser.add_argument('demo_file', nargs='+', default=[], type=argparse.FileType('r'), help="the demo file")
  parser.add_argument('--json', action="store_true", help="export to JSON file in current working directory")

  if len(sys.argv)==1:
      parser.print_help(sys.stderr)
      sys.exit(1)

  args = parser.parse_args()

  for item in args.demo_file:
      d = Demo()
      d.parse(item.name)

      out_name = Path(item.name).stem + '.json'

      if args.json:
          print(f"creating {out_name}")
          with open('./' + out_name, 'w', encoding='utf-8') as f:
              json.dump(d.__dict__, f, ensure_ascii=False, indent=4, cls=BytesEncoder)
      else:
        pp.pprint(d.__dict__)