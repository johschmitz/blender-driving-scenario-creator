# Changelog

## [Unreleased]

## [0.28.5] - 2025-05-20

### Fixed

- Crashing 4-way junction tool

## [0.28.4] - 2025-03-16

### Fixed

- Road sign texture creation failing in Blender 4.3.x

## [0.28.3] - 2025-03-16

### Fixed

- Snapping based setting of connecting roads start and end widths

## [0.28.2] - 2025-01-14

### Fixed

- Missing thumbnails and textures for road signs and road stencils due to
  Github's Ubuntu runner image upate

## [0.28.1] - 2025-01-09

### Fixed

- Direct junction roads not working
- Parampoly3 geometry roads not working

## [0.28.0] - 2024-12-04

### Added

- Tool for creating traffic lights
- Tool for painting road stencils, i.e, arrows on the road surface

## [0.27.2] - 2024-10-23

### Fixed

- 4-way junction tool not working with new lane offset

## [0.27.1] - 2024-10-19

### Fixed

- Sign tool not working with new lane offset

## [0.27.0] - 2024-10-08

### Added

- Integer lane offset in road creation tool which can be used to build left
  turning lanes
- Cross section template for junction incoming roads with an opening left
  turning lane

## [0.26.1] - 2024-09-21

### Fixed

- Road width visualization during road snapping with mouse pointer

## [0.26.0] - 2024-09-11

### Added

- New on-ramp and off-ramp cross section templates

### Fixed

- On-ramp and off-ramp cross section lane connections
- Clean up, i.e., remove, broken road links during export

## [0.25.0] - 2024-07-08

### Added

- Tool for creating stop lines that have a reference to a stop sign

### Fixed

- Refactoring bug in split road creation code leading to crash of road creation
  tool

## [0.24.1] - 2024-03-07

### Fixed

- Junction connecting road to junction joint left lane snapping

## [0.24.0] - 2024-02-29

### Added

- Tool for creating road signs which are placed by snapping to a road geometry
- Small collection of road signs from German sign catalog "VzKat" (speedlimits,
end of restrictions, stop, yield, right of way)

## [0.23.1] - 2023-11-22

### Fixed

- Do not set junction vertex creases for Blender 4.0.1 compatiblity
- Export of .obj files (used for .osgb converter) in Blender 4.0.1
- Wrong sign in elevation profile calculation of junction surface boundary

## [0.23.0] - 2023-10-16

### Added

- New triple clothoid road geometry tool with G2 continuity (curvature
  continuity) at both ends

### Changed

- Make junction boundary based on three segment G2 clothoid curve, use Hermite
  interpolation for the boundary elevation and roughly triangulate the junction
  surface.
- Use newly added triple clothoid road geometry for junction connecting roads

### Fixed

- Junction connecting road snapping for left lanes
- Road sampling when curvature is 0 at start of non straight line geometry
- Curvature calculation of parampoly3 geometry
- Sign of snapping curvature at road start

## [0.22.0] - 2023-10-06

### Changed

- After a rewrite the junction connection road tool does now create single lane
  connecting roads. Also junction joints now have lane information to decouple
  connecting road snapping and creation from incoming roads.

### Fixed

- Bug in changing number of left lanes in road cross section
- Creation of 4-way junction for non symmetric road cross sections

## [0.21.0] - 2023-06-27

### Added

- Operator for multi geometry ParamPoly3 geometry roads

### Fixed

- Heading issue with multi geometry clothoid roads resulting in broken OpenDRIVE
  export

## [0.20.0] - 2023-05-18

### Added

- Possibility to create roads with multiple geometry sections (in this version
  the type of the curve for each section will be identical)
- Holding <kbd>Shift</kbd> and click to add an additional section to the road you
  are currently editing
- Adjusting end heading of clothoid geometries (only for Hermite solver) by
  holding <kdb>Shift</kdb> and <kbd>Mousewheel Up/Down</kbd>

### Changed

- __Adjusting start heading of road is now done by holding <kbd>Alt</kbd>
  instead of <kbd>Shift</kbd> since <kbd>Shift</kbd> is now being used for
  adding new geometry sections__

## [0.19.1] - 2023-03-04

### Fixed

- Init action which broke during initial pedestrian implementation
- Do not link roads when snapping to grid. This fixes a bug where we would
  disable the road snapping while snapping to the grid (holding <kbd>Ctrl</kbd>)
  but the roads would sometimes still be linked when touched with the mouse
  pointer.

## [0.19.0] - 2023-03-04

### Added

- Operator and export of pedestrian OpenSCENARIO entities

### Changed

- Avoid snapping to roads when grid snapping is active (holding <kbd>Ctrl</kbd>)
- Connecting roads are not exported to 3D static scene model anymore

### Fixed

- Scenariogeneration renaming enum xosc.FollowMode.follow to
  xosc.FollowingMode.follow in scenariogeneration lib version 0.11.0. __Please
  update the scenariogeneration dependency in your Blender installation,
  otherwise OpenSCENARIO trajectory export will fail.__

## [0.18.1] - 2023-02-24

### Changed

- Modification of the start heading by holding <kbd>Shift</kbd> is now disabled
  when the road is snapped at the start point. This prevents the creation of
  non-compliant OpenDRIVE and side effects with road and lane linking.

### Fixed

- Double solid road markings

## [0.18.0] - 2023-02-22

### Added

- Cross sections for building a closed autobahn exit and entry "wedge" area with
  3 direct junctions

### Changed

- Rewrite of OpenDRIVE export lane linking to enable non linked lanes and
  autobahn exit "wedge" area

### Fixed

- Clean up of old direct junction link when connecting a new road without direct
  junction
- Linking of split (direct junction) roads

## [0.17.2] - 2023-01-25

### Fixed

- Mashup of track and vehicle 3D models during glTF export

## [0.17.1] - 2022-12-12

### Changed

- Snapped roads with heading in the wrong direction are now prevented
- Temporary .obj and .mtl files created during export of .osgb files (via
  osgconv) now removed after the conversion

### Fixed

- Some edge cases where clothoid or elevation calculation blows up

## [0.17.0] - 2022-12-07

### Added

- Emit GUI error when direct junction export failed due to missing connection

### Changed

- Four way junction now based on the generic junction tools with explicitly
  modelled junction connecting roads
- Renamed "junction connection" to "junction connecting road" to better match
  OpenDRIVE standard

### Fixed

- Division by zero resulting from zero road length edge case

## [0.16.0] - 2022-11-16

### Added

- Visualization of elevation of start point (also visible and changed when
  holding <kbd>S</kbd> in road drawing tool and moving the mouse)
- Make roads which are snapped both at start and end connect smoothly using a
  cubic Hermite spline segment

### Changed

- Set vertex crease values of junction area corners to 1.0 to prepare for the
  usage of a subdivision surface modifier, which will allow modelling of smooth
  junction surfaces

## [0.15.0] - 2022-11-04

### Added

- Top level collection that groups the addon related collections
- Explicit storage of addon version as part of the top level collection and
  hence in the .blend file
- Ability to properly place cars on a slope by taking the road normal vector
  into account for the 3D rotation

### Changed

- Improved the algorithm for junction area boundary calculation, it now supports
  the most usual convex and concave shapes
- Improved help status text for road and junction tools, now mentions that the
  view center can be move while the tool is active with the shortcut
  <kbd>Alt</kbd> + <kbd>Middlemouse</kbd>

### Fixed

- Invalid car and generic junction area mesh which was breaking during glTF
  export

## [0.14.1] - 2022-10-05

### Fixed

- Export of glTF assets (3D mesh files) for Blender 3.2+ versions

## [0.14.0] - 2022-10-03

### Added

- New operators to build generic junctions, a junction area tool based on
  selecting incoming roads and a junction connection tool which creates the
  connecting roads inside of junctions

### Changed

- Enable finishing trajectory by pressing <kbd>Space</kbd> (finishing with
  <kbd>Return</kbd> is still possible)
- Slightly update extension UI menu layout

## [0.13.0] - 2022-08-02

### Added

- Helpful vertical lines to better visualize the elevation during road drawing

### Changed

- Allow exporting 4-way junctions with a missing connection to easily build
  T-junctions until the availability of better junction tooling

## [0.12.0] - 2022-07-22

### Fixed

- Creating degenerate arc road with infinite radius not possible (would throw
  divide by zero exception)

### Added

- Enable changing the heading at the road start by holding <kbd>Shift</kbd>

## [0.11.1] - 2022-06-22

### Fixed

- Missing shoulder in on-ramp cross section template
- Crashing export of Autobahn on-ramps/entries

## [0.11.0] - 2022-06-21

### Added

- Opening and closing of (new) lanes to create exit and entry lanes
- Splitting and merging of roads at the beginning or end to connect on-ramps and
  off-ramps, exported as OpenDRIVE direct junctions
- Exemplary road cross section templates for building an RQ31 Autobahn exit

### Fixed

- Lane ID signs in GUI popup

## [0.10.2] - 2022-05-25

### Fixed

- OpenSCENARIO init action to let cars drive in the direction they have been
  placed when no trajectory is attached

## [0.10.1] - 2022-02-16

### Fixed

- Add polyline trajectory point headings which are now required for correct
  playback in esmini

## [0.10.0] - 2022-02-06

### Added

- Additional clothoid road operator using forward solver based on the curvature
  of the predecessor road section

### Fixed

- Avoid rendering blowup when start and end angle of clothoid roads are
  identical, notify user that no valid solution has been found
- Moving with <kbd>ALT</kbd>+<kbd>MIDDLEMOUSE</kbd> to only move on mouse button
  release

## [0.9.0] - 2022-01-23

### Added

- Double line road mark type "solid solid"
- Property for road mark weight (standard and bold)
- Property for road mark color (available: white and yellow)

### Fixed

- Initial pitch and roll of vehicle is adopted from road surface

## [0.8.0] - 2022-01-02

### Added

- Modifying elevation of roads using <kbd>E</kbd>(perspective) or
  <kbd>S</kbd>(sideview) key
- Trajectory operators can be used on elevated roads

### Changed

- Limit start and end endpoint to be not more than 10km apart

## [0.7.2] - 2021-11-07

### Fixed

- End point constraining of arc geometry

## [0.7.1] - 2021-10-25

### Fixed

- Remove duplicate road vertices
- Subdivide lane faces of long roads to avoid rendering issues

## [0.7.0] - 2021-10-24

### Added

- Operator for creating clothoid (Euler Spiral) roads

### Changed

- The road operators for all geometries are now unified and the mesh is sampled
  along the road coordinate system. This also means that all road operators now
  use the cross section configuration UI and support the selected cross
  sections.

## [0.6.0] - 2021-09-06

### Added

- Presets for road cross sections
- Some typical German standardized RAL and RAA road cross sections (RQ9, RQ11,
  RQ31, RQ36, RQ43.5)

### Fixed

- Export crashing when no trajectories exist

## [0.5.0] - 2021-08-30

### Added

- Operator for creating NURBS trajectories

### Fixed

- Path pointing from .xosc file to .xodr file (LogicFile path) not being written
  as relative path

## [0.4.0] - 2021-08-25

### Added

- Operator for creating polyline trajectories

### Fixed

- Icon .png files missing in previous releases now contained in repository and
  release .zip file

## [0.3.0] - 2021-08-17

### Added

- Configurable name, color and initial speed for car objects
- Export of car models with different colors

## [0.2.0] - 2021-08-08

### Added

- Option to export meshes as .fbx files
- Option to export meshes as .gltf files
- Configurable number and type of lanes for straight roads
- Configurable road mark type for straight roads (solid and broken)

## [0.1.1] - 2021-06-21

### Fixed

- Avoid exporter crash and display error message if junction is not fully
  connected

## [0.1.0] - 2021-06-11

### Added

- Operator for creating straight line roads
- Operator for creating arc roads
- Operator for creating 4-way junctions
- Road and junction snapping
- Snapping to grid with <kbd>Ctrl</kbd> modifier key
- Solid lane lines for arc and straight roads
- Operator for creating cars
- Export OpenSCENARIO and OpenDRIVE files using scenariogeneration lib
- Export meshes as .osgb files for esmini using osgconv

[Unreleased]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.28.5...HEAD
[0.28.5]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.28.4...v0.28.5
[0.28.4]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.28.3...v0.28.4
[0.28.3]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.28.2...v0.28.3
[0.28.2]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.28.1...v0.28.2
[0.28.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.28.0...v0.28.1
[0.28.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.27.2...v0.28.0
[0.27.2]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.27.1...v0.27.2
[0.27.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.27.0...v0.27.1
[0.27.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.26.1...v0.27.0
[0.26.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.26.0...v0.26.1
[0.26.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.25.0...v0.26.0
[0.25.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.24.1...v0.25.0
[0.24.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.24.0...v0.24.1
[0.24.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.23.1...v0.24.0
[0.23.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.23.0...v0.23.1
[0.23.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.22.0...v0.23.0
[0.22.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.21.0...v0.22.0
[0.21.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.20.0...v0.21.0
[0.20.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.19.1...v0.20.0
[0.19.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.19.0...v0.19.1
[0.19.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.18.1...v0.19.0
[0.18.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.18.0...v0.18.1
[0.18.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.17.2...v0.18.0
[0.17.2]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.17.1...v0.17.2
[0.17.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.17.0...v0.17.1
[0.17.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.15.0...v0.16.0
[0.15.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.14.1...v0.15.0
[0.14.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.14.0...v0.14.1
[0.14.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.11.1...v0.12.0
[0.11.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.10.2...v0.11.0
[0.10.2]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.10.1...v0.10.2
[0.10.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.7.2...v0.8.0
[0.7.2]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/johschmitz/blender-driving-scenario-creator/releases/tag/v0.1.0
