#!/usr/bin/env bash

echo "Converting entity SVGs to preview PNGs..."

# Get the directory of the script and cd into it
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

if ! command -v rsvg-convert >/dev/null 2>&1; then
    echo "Error: install librsvg (rsvg-convert) to render SVGs. On macOS use 'brew install librsvg'; on Ubuntu use 'sudo apt install librsvg2-bin'." >&2
    exit 1
fi

if command -v magick >/dev/null 2>&1; then
    IMAGEMAGICK=magick
elif command -v convert >/dev/null 2>&1; then
    IMAGEMAGICK=convert
else
    echo "Error: install ImageMagick to convert entity SVGs to PNG." >&2
    exit 1
fi

# Process all .svg files in the script's subdirectories
for file in "$SCRIPT_DIR"/*/*.svg
do
    if [[ "$file" == "$SCRIPT_DIR"/vehicles/entity_vehicle_*.svg ]]; then
        echo "Rendering vehicle outline preview: $file"
        output_file="${file%.svg}_preview.png"
        rendered_file="$TEMP_DIR/$(basename "${file%.svg}").png"
        rsvg-convert --output "$rendered_file" "$file"
        "$IMAGEMAGICK" "$rendered_file" -resize 256 "$output_file"
        continue
    fi
    echo "$file"
    rendered_file="$TEMP_DIR/$(basename "${file%.svg}").png"
    rsvg-convert --output "$rendered_file" "$file"
    "$IMAGEMAGICK" "$rendered_file" -resize 256 "${file%.svg}_preview.png"
done

echo "Done."
