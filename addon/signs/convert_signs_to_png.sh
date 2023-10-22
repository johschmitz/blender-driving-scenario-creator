#!/bin/sh

for file in */*.svg
do
    convert -background none -antialias "${file}" "${file%.svg}_texture.png"
    convert -background none -antialias -crop 50%x100%+0+0 "${file}" "${file%.svg}_preview.png"
done