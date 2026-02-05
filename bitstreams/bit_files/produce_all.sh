#!/bin/bash

for file in ../ariane_*.bit; do
  echo "Flashing: $file"
  ./flash.sh "$file"
done
