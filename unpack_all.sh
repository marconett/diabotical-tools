#!/bin/bash

for filename in _packs/*.dbp; do
  ./dbp-packer.py unpack "$filename" _unpacked
done