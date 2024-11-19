#!/usr/bin/env bash

echo "Converting stencils SVGs to preview PNGs..."

# Get the directory of the script and cd into it
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Process all .svg files in the script's subdirectories
for file in $SCRIPT_DIR/*/*.svg
do
    echo ${file}
    convert -background none -resize 400 -antialias "${file}" "${file%.svg}_preview.png"
done

echo "Done."