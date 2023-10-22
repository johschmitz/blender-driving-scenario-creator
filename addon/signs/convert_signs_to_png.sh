#!/usr/bin/env bash

echo "Converting road sign textures to PNG..."

# Get the directory of the script and cd into it
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Process all .svg files in the script's subdirectories
for file in $SCRIPT_DIR/*/*.svg
do
    echo ${file}
    convert -background none -antialias "${file}" "${file%.svg}_texture.png"
    convert -background none -antialias -crop 50%x100%+0+0 "${file}" "${file%.svg}_preview.png"
done

echo "Done."