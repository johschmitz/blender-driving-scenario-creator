#!/usr/bin/env bash

cp -r addon blender-driving-scenario-creator
./blender-driving-scenario-creator/signs/convert_signs_to_png.sh
rm -rf blender-driving-scenario-creator/signs/convert_signs_to_png.sh
rm -rf blender-driving-scenario-creator/signs/*/*.svg
zip -r blender-driving-scenario-creator-$RELEASE_VERSION.zip blender-driving-scenario-creator/
rm -rf blender-driving-scenario-creator/
