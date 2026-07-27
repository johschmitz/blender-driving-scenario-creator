#!/usr/bin/env bash

cp -r addon blender-driving-scenario-creator
./blender-driving-scenario-creator/signs/convert_signs_to_png.sh
./blender-driving-scenario-creator/stencils/convert_stencils_to_png.sh
./blender-driving-scenario-creator/entities/convert_entities_to_png.sh
rm -rf blender-driving-scenario-creator/signs/convert_signs_to_png.sh
rm -rf blender-driving-scenario-creator/signs/*/*.svg
rm -rf blender-driving-scenario-creator/entities/convert_entities_to_png.sh
rm -rf blender-driving-scenario-creator/entities/*/*.svg
zip -r blender-driving-scenario-creator-$RELEASE_VERSION.zip blender-driving-scenario-creator/
rm -rf blender-driving-scenario-creator/
