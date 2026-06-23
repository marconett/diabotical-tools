#!/usr/bin/python3

"""
ParseRBE (Diabotical Map Parsing Lib)
Copyright (C) 2020 Sean Berwick <stringtheory@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import struct
import math
import copy
import sys
import colorsys
import gzip
import json
import argparse
from io import BytesIO
from pathlib import Path, PureWindowsPath

class MapObject:

    # TODO before organizing the architecture/porting:
    ############
    # AddBlocks(xyz, xyz) ----- Array or box
    # addTeleporter(xyz entrance, w, h, xyz exit, dir)
    # Set target
    # Set action
    # Clear properties
    # Delete blocks
    # Delete entity
    # https://liquipedia.net/arenafps/Diabotical_map_editing

    ##############
    # ADD: BLOCK #
    ##############
    def AddBlock(self, x, y, z, block_type=1, mats=None, mat_offs=None, orient=2):
        self.block_count += 1

        if mats == None:
            mats = {
                'front': 1,
                'left': 1,
                'back': 1,
                'right': 1,
                'top': 1,
                'bottom': 1
            }

        if mat_offs == None:
            mat_offs = {
                'front': {'x': 0, 'y': 0},
                'left': {'x': 0, 'y': 0},
                'back': {'x': 0, 'y': 0},
                'right': {'x': 0, 'y': 0},
                'top': {'x': 0, 'y': 0},
                'bottom': {'x': 0, 'y': 0}
            }

        newBlock = {
            'x': x,
            'y': y,
            'z': z,
            'type': block_type,
            'u1': 0,
            'mats': mats,
            'u2': 0,
            'mat_offs': mat_offs,
            'orient': orient,
            'u3': 0,
            'u4': 0
        }
        self.blocks.append(newBlock)

    ###############
    # ADD: ENTITY #
    ###############
    def AddEntity(self, name, x=0.0, y=0.0, z=0.0, xrot=0.0, yrot=0.0, zrot=0.0, xscale=1.0, yscale=1.0, zscale=1.0, properties=[]):
        self.entity_count += 1
        newEnt = {
            'name_len': len(name),
            'name':     name,
            'x':        x,
            'y':        y,
            'z':        z,
            'xrot':     xrot,
            'yrot':     yrot,
            'zrot':     zrot,
            'xscale':   xscale,
            'yscale':   yscale,
            'zscale':   zscale,
            'property_count':   len(properties),
            'properties':       properties
        }
        self.entities.append(newEnt)

    ##################
    # FIND: ENTITIES #
    ##################
    def FindEntities(self, name):
        result = []
        for e in self.entities:
            if name.lower() in e['name'].lower():
                result.append(e)
        return result

    ###########################
    # LOAD & PARSE A MAP FILE #
    ###########################
    def Load(self, f):

        with open(f, 'rb') as f:
            self.rebm               = f.read(4).decode("utf-8")
            self.ver                = decodeInt(f.read(4))
            self.u1                 = decodeInt(f.read(4))

            print(f"Map Format Version: {self.ver}")

            self.padding1         = decodeInt(f.read(4))

            if self.ver > 21:
              self.author_length    = decodeInt(f.read(4))
              self.author_name      = f.read(self.author_length).decode("utf-8")
              self.padding2         = decodeInt(f.read(8))

              f = gzip.GzipFile(fileobj=f)

            self.material_count     = decodeInt(f.read(1))
            self.materials          = []
            for i in range(self.material_count - 1):
                c = decodeInt(f.read(4))
                m = {
                    'name_len': c,
                    'name':     f.read(c).decode("utf-8")
                    }
                self.materials.append(m)

            self.u2                 = decodeInt(f.read(4))

            self.bounds = {'minx': 0.0, 'maxx': 0.0, 'miny': 0.0, 'maxy': 0.0,  'minz': 0.0, 'maxz': 0.0}

            print(f"block_count offset: 0x{f.tell():08x}")
            self.block_count        = decodeInt(f.read(4))

            self.blocks             = []
            for i in range(self.block_count): # 53 bytes per block
                b = {
                    'x':        decodeInt(f.read(4)),
                    'y':        decodeInt(f.read(4)),
                    'z':        decodeInt(f.read(4)),
                    'type':     decodeInt(f.read(1)),
                    'u1':       decodeInt(f.read(12)),
                    'mats':     {
                        'front': decodeInt(f.read(1)),
                        'left': decodeInt(f.read(1)),
                        'back': decodeInt(f.read(1)),
                        'right': decodeInt(f.read(1)),
                        'top': decodeInt(f.read(1)),
                        'bottom': decodeInt(f.read(1)),
                    },
                    'u2':       decodeInt(f.read(1)),
                    'mat_offs': { # like a position on a sprite sheet
                        'front': {
                            'x': decodeInt(f.read(1)),
                            'y': decodeInt(f.read(1))
                        },
                        'left': {
                            'x': decodeInt(f.read(1)),
                            'y': decodeInt(f.read(1))
                        },
                        'back': {
                            'x': decodeInt(f.read(1)),
                            'y': decodeInt(f.read(1))
                        },
                        'right': {
                            'x': decodeInt(f.read(1)),
                            'y': decodeInt(f.read(1))
                        },
                        'top': {
                            'x': decodeInt(f.read(1)),
                            'y': decodeInt(f.read(1))
                        },
                        'bottom': {
                            'x': decodeInt(f.read(1)),
                            'y': decodeInt(f.read(1))
                        },
                    },
                }

                if self.ver > 24:
                  b['u3'] = decodeInt(f.read(6))
                  b['orient'] = decodeInt(f.read(1))
                  b['u4'] = decodeInt(f.read(2))
                else:
                  b['orient'] = decodeInt(f.read(1))
                  b['u3'] = decodeInt(f.read(1))

                self.blocks.append(b)
                self.bounds['minx'] = b['x'] if b['x'] < self.bounds['minx'] or self.bounds['minx'] == 0 else self.bounds['minx']
                self.bounds['maxx'] = b['x'] if b['x'] > self.bounds['maxx'] or self.bounds['maxx'] == 0 else self.bounds['maxx']
                self.bounds['miny'] = b['y'] if b['y'] < self.bounds['miny'] or self.bounds['miny'] == 0 else self.bounds['miny']
                self.bounds['maxy'] = b['y'] if b['y'] > self.bounds['maxy'] or self.bounds['maxy'] == 0 else self.bounds['maxy']
                self.bounds['minz'] = b['z'] if b['z'] < self.bounds['minz'] or self.bounds['minz'] == 0 else self.bounds['minz']
                self.bounds['maxz'] = b['z'] if b['z'] > self.bounds['maxz'] or self.bounds['maxz'] == 0 else self.bounds['maxz']

            # 2D slices (BlockInfo2d): per-cell room id + optional camera hint
            print(f"slice_count offset: 0x{f.tell():08x}")
            self.slice_count        = decodeInt(f.read(4))
            self.slices             = []
            for i in range(self.slice_count):
                s = {
                    'sx':    decodeInt(f.read(4)),
                    'sy':    decodeInt(f.read(4)),
                    'sroom': decodeInt(f.read(4)),
                }
                if self.ver > 11:
                    c = decodeInt(f.read(4))
                    s['camera_hint'] = f.read(c).decode("utf-8")
                self.slices.append(s)

            print(f"entity_count offset: 0x{f.tell():08x}")
            self.entity_count       = decodeInt(f.read(4))
            self.entities           = []
            for i in range(self.entity_count):
                c = decodeInt(f.read(4))
                e = {
                    'name_len': c,
                    'name':     f.read(c).decode("utf-8"),
                    'x':        decodeFloat(f.read(4)),
                    'y':        decodeFloat(f.read(4)),
                    'z':        decodeFloat(f.read(4)),
                    'xrot':     radToDeg(decodeFloat(f.read(4))),
                    'yrot':     radToDeg(decodeFloat(f.read(4))),
                    'zrot':     radToDeg(decodeFloat(f.read(4))),
                    'xscale':   decodeFloat(f.read(4)),
                    'yscale':   decodeFloat(f.read(4)),
                    'zscale':   decodeFloat(f.read(4)),
                }
                e['property_count']         = decodeInt(f.read(4))
                e['properties']             = []
                for j in range(e['property_count']):
                    p = {}
                    c = decodeInt(f.read(4))
                    p['name_len'] = c
                    p['name'] = f.read(c).decode("utf-8")
                    c = decodeInt(f.read(4))
                    p['val_len'] = c
                    p['val'] = f.read(c).decode("utf-8")
                    e['properties'].append(p)
                self.entities.append(e)

            # audio propagation graph: per-node grid coord + connected coords
            print(f"audio_count offset: 0x{f.tell():08x}")
            self.audio_count        = decodeInt(f.read(4))
            self.audio_raw          = []
            for i in range(self.audio_count):
                a = {
                    'audio_raw': f.read(12),
                    'child_count': decodeInt(f.read(4)),
                    'children': []
                }
                for j in range(a['child_count']):
                    a['children'].append(f.read(12))
                self.audio_raw.append(a)

            # navmesh: length-prefixed Detour blob (kept raw; 0 bytes on most maps)
            print(f"navigation_size offset: 0x{f.tell():08x}")
            self.navigation_size    = decodeInt(f.read(4))
            self.navmesh            = f.read(self.navigation_size)

            # discovery / per-height-level cells (what the minimap is drawn from)
            print(f"minimap_layer_count offset: 0x{f.tell():08x}")
            self.minimap_bounds = { 'minx': 0.0, 'maxx': 0.0, 'miny': 0.0, 'maxy': 0.0 }
            self.minimap_layer_count    = decodeInt(f.read(4))
            self.minimap_layers         = []
            for i in range(self.minimap_layer_count):
                ly = {
                    'height': decodeInt(f.read(4)),
                    'point_count': decodeInt(f.read(4)),
                    'points': []
                }
                for j in range(ly['point_count']):
                    p = {
                        'x': decodeInt(f.read(4)),
                        'y': decodeInt(f.read(4))
                    }
                    ly['points'].append(p)
                    self.minimap_bounds['minx'] = p['x'] if p['x'] < self.minimap_bounds['minx'] or self.minimap_bounds['minx'] == 0 else self.minimap_bounds['minx']
                    self.minimap_bounds['maxx'] = p['x'] if p['x'] > self.minimap_bounds['maxx'] or self.minimap_bounds['maxx'] == 0 else self.minimap_bounds['maxx']
                    self.minimap_bounds['miny'] = p['y'] if p['y'] < self.minimap_bounds['miny'] or self.minimap_bounds['miny'] == 0 else self.minimap_bounds['miny']
                    self.minimap_bounds['maxy'] = p['y'] if p['y'] > self.minimap_bounds['maxy'] or self.minimap_bounds['maxy'] == 0 else self.minimap_bounds['maxy']
                self.minimap_layers.append(ly)

            # level collision hulls (static geometry players/projectiles hit)
            self.level_hull_count   = 0
            self.level_hulls        = []
            if self.ver > 17:
                print(f"level_hull_count offset: 0x{f.tell():08x}")
                self.level_hull_count   = decodeInt(f.read(4))
                for i in range(self.level_hull_count):
                    self.level_hulls.append(readPlaneSet(f, self.ver))

            # moving-entity collision hulls (grouped per entity: movers, doors, liquids)
            self.moving_hull_group_count = 0
            self.moving_hull_groups      = []
            if self.ver > 20:
                print(f"moving_hull_group_count offset: 0x{f.tell():08x}")
                self.moving_hull_group_count = decodeInt(f.read(4))
                for i in range(self.moving_hull_group_count):
                    c = decodeInt(f.read(4))
                    g = {
                        'name':  f.read(c).decode("utf-8"),
                        'hulls': []
                    }
                    planeset_count = decodeInt(f.read(4))
                    for j in range(planeset_count):
                        g['hulls'].append(readPlaneSet(f, self.ver))
                    self.moving_hull_groups.append(g)

            # Should be empty on all known versions; preserved so unknown trailing
            # data from a future map format still round-trips through Save().
            self.trailing = f.read()
            if len(self.trailing):
                print(f"warning: {len(self.trailing)} unparsed trailing bytes preserved")

    def EmptyMap(self):
        self.material_count = 0
        self.materials = []
        self.block_count = 0
        self.blocks = []
        self.slice_count = 0
        self.slices = []
        self.entity_count = 0
        self.entities = []
        self.audio_count = 0
        self.audio_raw = []
        self.navigation_size = 0
        self.navmesh = bytearray()
        self.minimap_layer_count = 0
        self.minimap_layers = []
        self.level_hull_count = 0
        self.level_hulls = []
        self.moving_hull_group_count = 0
        self.moving_hull_groups = []
        self.trailing = bytearray()

    ##########################
    # PACK & SAVE A MAP FILE #
    ##########################
    def Save(self, f):

        gf = BytesIO()  # the decompressed body
        if True:
            gf.write(encodeInt(self.material_count, 1))
            for m in self.materials:
                gf.write(encodeInt(m['name_len'], 4))
                gf.write(encodeString(m['name']))

            gf.write(encodeInt(self.u2, 4))

            gf.write(encodeInt(self.block_count, 4))
            for b in self.blocks:
                gf.write(encodeInt(b['x'], 4))
                gf.write(encodeInt(b['y'], 4))
                gf.write(encodeInt(b['z'], 4))
                gf.write(encodeInt(b['type'], 1))
                gf.write(encodeInt(b['u1'], 12))
                gf.write(encodeInt(b['mats']['front'], 1))
                gf.write(encodeInt(b['mats']['left'], 1))
                gf.write(encodeInt(b['mats']['back'], 1))
                gf.write(encodeInt(b['mats']['right'], 1))
                gf.write(encodeInt(b['mats']['top'], 1))
                gf.write(encodeInt(b['mats']['bottom'], 1))
                gf.write(encodeInt(b['u2'], 1))
                gf.write(encodeInt(b['mat_offs']['front']['x'], 1))
                gf.write(encodeInt(b['mat_offs']['front']['y'], 1))
                gf.write(encodeInt(b['mat_offs']['left']['x'], 1))
                gf.write(encodeInt(b['mat_offs']['left']['y'], 1))
                gf.write(encodeInt(b['mat_offs']['back']['x'], 1))
                gf.write(encodeInt(b['mat_offs']['back']['y'], 1))
                gf.write(encodeInt(b['mat_offs']['right']['x'], 1))
                gf.write(encodeInt(b['mat_offs']['right']['y'], 1))
                gf.write(encodeInt(b['mat_offs']['top']['x'], 1))
                gf.write(encodeInt(b['mat_offs']['top']['y'], 1))
                gf.write(encodeInt(b['mat_offs']['bottom']['x'], 1))
                gf.write(encodeInt(b['mat_offs']['bottom']['y'], 1))

                if self.ver > 24:
                  gf.write(encodeInt(b['u3'], 6))
                  gf.write(encodeInt(b['orient'], 1))
                  gf.write(encodeInt(b['u4'], 2))
                else:
                  gf.write(encodeInt(b['orient'], 1))
                  gf.write(encodeInt(b['u3'], 1))



            gf.write(encodeInt(self.slice_count, 4))
            for s in self.slices:
                gf.write(encodeInt(s['sx'], 4))
                gf.write(encodeInt(s['sy'], 4))
                gf.write(encodeInt(s['sroom'], 4))
                if self.ver > 11:
                    hint = encodeString(s.get('camera_hint', ''))
                    gf.write(encodeInt(len(hint), 4))
                    gf.write(hint)

            gf.write(encodeInt(self.entity_count, 4))
            for e in self.entities:
                gf.write(encodeInt(e['name_len'], 4))
                gf.write(encodeString(e['name']))
                gf.write(encodeFloat(e['x']))
                gf.write(encodeFloat(e['y']))
                gf.write(encodeFloat(e['z']))
                gf.write(encodeFloat(degToRad(e['xrot'])))
                gf.write(encodeFloat(degToRad(e['yrot'])))
                gf.write(encodeFloat(degToRad(e['zrot'])))
                gf.write(encodeFloat(e['xscale']))
                gf.write(encodeFloat(e['yscale']))
                gf.write(encodeFloat(e['zscale']))
                gf.write(encodeInt(e['property_count'], 4))
                for p in e['properties']:
                    gf.write(encodeInt(p['name_len'], 4))
                    gf.write(encodeString(p['name']))
                    gf.write(encodeInt(p['val_len'], 4))
                    gf.write(encodeString(p['val']))

            gf.write(encodeInt(self.audio_count, 4))
            for a in self.audio_raw:
                gf.write(a['audio_raw'])
                gf.write(encodeInt(a['child_count'], 4))
                for c in a['children']:
                    gf.write(c)

            gf.write(encodeInt(self.navigation_size, 4))
            gf.write(self.navmesh)

            gf.write(encodeInt(self.minimap_layer_count, 4))
            for ly in self.minimap_layers:
                gf.write(encodeInt(ly['height'], 4))
                gf.write(encodeInt(ly['point_count'], 4))
                for p in ly['points']:
                    gf.write(encodeInt(p['x'], 4))
                    gf.write(encodeInt(p['y'], 4))

            if self.ver > 17:
                gf.write(encodeInt(self.level_hull_count, 4))
                for ps in self.level_hulls:
                    writePlaneSet(gf, ps, self.ver)

            if self.ver > 20:
                gf.write(encodeInt(self.moving_hull_group_count, 4))
                for g in self.moving_hull_groups:
                    name = encodeString(g['name'])
                    gf.write(encodeInt(len(name), 4))
                    gf.write(name)
                    gf.write(encodeInt(len(g['hulls']), 4))
                    for ps in g['hulls']:
                        writePlaneSet(gf, ps, self.ver)

            gf.write(self.trailing)

        body = gf.getbuffer()

        with open(f, 'wb') as out:
            out.write(encodeString(self.rebm))
            out.write(encodeInt(self.ver, 4))
            out.write(encodeInt(self.u1, 4))
            out.write(encodeInt(self.padding1, 4))

            if self.ver > 21:
                # author block + name2 + gzip marker, then the gzip-compressed body
                author = encodeString(self.author_name)
                out.write(encodeInt(len(author), 4))
                out.write(author)
                out.write(encodeInt(self.padding2, 8))
                gzipped = BytesIO()
                with gzip.GzipFile(mode='wb', fileobj=gzipped) as gz:
                    gz.write(body)
                out.write(gzipped.getbuffer())
            else:
                # version <= 21 stores the body uncompressed with no author block
                out.write(body)

    def DrawMinimap(self, name):
        from PIL import Image, ImageDraw, ImageFilter

        layer_count = len(self.minimap_layers)

        if layer_count > 0:
          colors = getColorArray(layer_count)

          factor = 16
          width = (abs(self.minimap_bounds['minx']) + self.minimap_bounds['maxx'])
          height = (abs(self.minimap_bounds['miny']) + self.minimap_bounds['maxy'])

          img = Image.new( mode = "RGB", size = (width, height) )
          draw = ImageDraw.Draw(img)


          for i, layer in enumerate(self.minimap_layers):
              for point in layer['points']:
                  x = (point['x'] + abs(self.minimap_bounds['minx']))
                  y = (point['y'] + abs(self.minimap_bounds['miny']))
                  draw.rectangle((x, y, x, y), fill=colors[i], outline=colors[i])

          img = img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
          img = img.resize((width*factor, height*factor), resample=0)
          img = img.filter(ImageFilter.ModeFilter(size=11))
          img = img.filter(ImageFilter.EDGE_ENHANCE)

          # img.show()
          img.save(name + ".png", "PNG")
        else:
          print("No minimap found in map file")

def encodeInt(data, bytes):
    return data.to_bytes(bytes, "little", signed=True)
def encodeFloat(data):
    return bytearray.fromhex(struct.pack('<f', data).hex())
def encodeString(data):
    return data.encode()
def decodeInt(data):
    return int.from_bytes(data, "little", signed=True)
def decodeUInt(data):
    return int.from_bytes(data, "little", signed=False)
def decodeFloat(data):
    return struct.unpack('<f', data)[0]
def decodeDouble(data):
    return struct.unpack('<d', data)[0]
def encodeUInt(data, bytes):
    return data.to_bytes(bytes, "little", signed=False)
def encodeDouble(data):
    return struct.pack('<d', data)
def degToRad(degrees):
    return degrees * math.pi / 180
def radToDeg(radians):
    return radians * 180 / math.pi

# A convex collision hull: levels::PlaneSet. Used by both the level-collision
# section and the per-moving-entity collision section. On disk it is a fixed
# 142-byte (138 for version < 23) double-precision header, then the owning
# entity name, 14 bytes of slide/stairs fields, then plane_count x 32-byte
# Plane records. A Plane is a half-space stored distance-first, then unit normal.
def readPlaneSet(f, ver):
    ps = {
        'id':            decodeUInt(f.read(4)),
        'max_radius':    decodeDouble(f.read(8)),
        'origin':        [decodeDouble(f.read(8)) for _ in range(3)],
        'origin_orig':   [decodeDouble(f.read(8)) for _ in range(3)],
        'aabb_min':      [decodeDouble(f.read(8)) for _ in range(3)],
        'block_pass':    decodeInt(f.read(1)),
        'block_fire':    decodeInt(f.read(1)),
        'aabb_extra':    [decodeDouble(f.read(8)) for _ in range(6)],  # aabb_max + rtree extents
        'clip':          decodeInt(f.read(4)),
        'collision_mask': decodeUInt(f.read(4)) if ver > 22 else 0,    # added in v23
    }
    c = decodeInt(f.read(4))
    ps['name']       = f.read(c).decode("utf-8")  # owning entity name
    ps['slide_type'] = decodeInt(f.read(4))
    ps['is_stairs']  = decodeInt(f.read(1))
    ps['stairs_yaw'] = decodeDouble(f.read(8))
    ps['has_target'] = decodeInt(f.read(1))
    plane_count = decodeInt(f.read(4))
    ps['planes'] = []
    for _ in range(plane_count):
        ps['planes'].append({
            'distance': decodeDouble(f.read(8)),
            'normal':   [decodeDouble(f.read(8)) for _ in range(3)],
        })
    return ps

def writePlaneSet(gf, ps, ver):
    gf.write(encodeUInt(ps['id'], 4))
    gf.write(encodeDouble(ps['max_radius']))
    for v in ps['origin']:      gf.write(encodeDouble(v))
    for v in ps['origin_orig']: gf.write(encodeDouble(v))
    for v in ps['aabb_min']:    gf.write(encodeDouble(v))
    gf.write(encodeInt(ps['block_pass'], 1))
    gf.write(encodeInt(ps['block_fire'], 1))
    for v in ps['aabb_extra']:  gf.write(encodeDouble(v))
    gf.write(encodeInt(ps['clip'], 4))
    if ver > 22:
        gf.write(encodeUInt(ps['collision_mask'], 4))
    name = encodeString(ps['name'])
    gf.write(encodeInt(len(name), 4))
    gf.write(name)
    gf.write(encodeInt(ps['slide_type'], 4))
    gf.write(encodeInt(ps['is_stairs'], 1))
    gf.write(encodeDouble(ps['stairs_yaw']))
    gf.write(encodeInt(ps['has_target'], 1))
    gf.write(encodeInt(len(ps['planes']), 4))
    for pl in ps['planes']:
        gf.write(encodeDouble(pl['distance']))
        for v in pl['normal']:  gf.write(encodeDouble(v))

def getColorArray(size):
    HSV_tuples = [(x * 1.0 / size, 0.5, 0.5) for x in range(size)]
    hex_out = []
    for rgb in HSV_tuples:
        rgb = map(lambda x: int(x * 255), colorsys.hsv_to_rgb(*rgb))
        hex_out.append('#%02x%02x%02x' % tuple(rgb))
    return hex_out


class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return json.JSONEncoder.default(self, obj)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='rbe-parser.py', description=".rbe map file parser for Diabotical")
    parser.add_argument('source', type=argparse.FileType('r'), help="the .rbe map file")
    parser.add_argument('--json', action=argparse.BooleanOptionalAction, help="export to JSON in current working directory (CAUTION: the file will be huge)")
    parser.add_argument('--minimap', action=argparse.BooleanOptionalAction, help="create a minimap png in current working directory ")
    parser.add_argument('--test', action=argparse.BooleanOptionalAction, help="Use any official map as a \"template\", delete it's content and write new map")

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    print("Parsing started ...")
    m = MapObject()
    m.Load(args.source.name)
    print("Done parsing")

    fileOut = str(Path(PureWindowsPath(args.source.name)).stem)

    if args.json:
        print("\ncreating json ...")
        with open('./' + fileOut + '.json', 'w', encoding='utf-8') as f:
            json.dump(m.__dict__, f, ensure_ascii=False, indent=4, cls=BytesEncoder)

    if args.minimap:
        print("\ncreating minimap ...")
        m.DrawMinimap(fileOut)

    if args.test:
        print("\ncreating test map ...")
        m.EmptyMap()
        m.AddBlock(10, 20, 30)
        m.Save('wo_ws_test.rbe')

    print("DONE")