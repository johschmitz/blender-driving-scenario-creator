#!/usr/bin/env bash

echo "Converting road sign textures to PNG..."

# Get the directory of the script and cd into it
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if ! command -v rsvg-convert >/dev/null 2>&1; then
    echo "Error: install librsvg (rsvg-convert) to render SVGs. On macOS use 'brew install librsvg'; on Ubuntu use 'sudo apt install librsvg2-bin'." >&2
    exit 1
fi

if command -v magick >/dev/null 2>&1; then
    IMAGEMAGICK=magick
elif command -v convert >/dev/null 2>&1; then
    IMAGEMAGICK=convert
else
    echo "Error: install ImageMagick to convert sign SVGs to PNG." >&2
    exit 1
fi
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Process all .svg files in the script's subdirectories
for file in "$SCRIPT_DIR"/*/*.svg
do
    echo "$file"
    rendered_file="$TEMP_DIR/$(basename "${file%.svg}").png"
    rsvg-convert --output "$rendered_file" "$file"
    cp "$rendered_file" "${file%.svg}_texture.png"
    "$IMAGEMAGICK" "$rendered_file" -crop 50%x100%+0+0 +repage "${file%.svg}_preview.png"
done

echo "Done."