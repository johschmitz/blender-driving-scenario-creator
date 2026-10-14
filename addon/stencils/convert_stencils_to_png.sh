#!/usr/bin/env bash

echo "Converting stencils SVGs to preview PNGs..."

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
    echo "Error: install ImageMagick to resize rendered stencil images." >&2
    exit 1
fi

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Process all .svg files in the script's subdirectories
for file in "$SCRIPT_DIR"/*/*.svg
do
    echo "$file"
    output_file="${file%.svg}_preview.png"
    rendered_file="$TEMP_DIR/$(basename "${file%.svg}").png"
    rsvg-convert --output "$rendered_file" "$file"
    "$IMAGEMAGICK" "$rendered_file" -resize 400 "$output_file"
done

echo "Done."