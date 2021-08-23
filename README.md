# Blender Driving Scenario Creator add-on

This [Blender](https://www.blender.org/) add-on lets you create OpenDRIVE and
OpenSCENARIO based scenarios for testing of advanced driver assistance systems
and autonomous driving functions.

## How to install

Let's assume that we work with a Debian based Linux distribution and Blender has
been [downloaded](https://www.blender.org/download/) and installed to

    /opt/blender/

Then we first need to install the
[scenarigeneration](https://github.com/pyoscx/scenariogeneration) library into
the Blender Python environment since the add-on uses the library as a backend to
write OpenDRIVE and OpenSCENARIO files. The scenariogeneration lib uses
pyclothoids which is written in C++ under the hood. Therefore make sure the
Python headers are installed to be able to compile pyclothoids during the
installation of scenariogeneration with pip

    sudo apt install python3.9-dev

then to make the pip installation coming with Blender find the headers

    export CPPFLAGS=-I/usr/include/python3.9/

The above two lines might be slightly different when using a non Debian based
Linux distribution. Next, navigate to your Blender included Python installation

    cd /opt/blender/2.93/python/bin

if pip is not there already then run

    sudo ./python3.9 -m ensurepip

now install the lib

    sudo -E ./pip3 install scenariogeneration

where the `-E` makes sudo preserve the exported environment variable. Note that
`sudo` is not required in case Blender is installed to the user home directory.

For the esmini export functionality we also need to install
[OpenSceneGraph](http://www.openscenegraph.org/) to have the `osgconv` tool
available. This is necessary because Blender is unable to directly export to the
.osgb scenegraph format, while esmini can only process this particular format.
On a Debian/Ubuntu/Mint system this can be achieved with

    sudo apt install openscenegraph

If you manually install OpenSceneGraph make sure that `osgconv` can be found
through your `PATH` environment variable, otherwise the export for esmini will
fail.

Finally download the driving scenario generator release .zip archive. Open
Blender and go to Edit -> Preferences -> Add-ons. Click "Install...". Select the
.zip archive and confirm.

## How to use

When you are in the Blender "Layout" workspace press <kbd>N</kbd> or click the
little arrow next to the navigation gizmo to toggle the sidebar. Click
<kbd>Driving Scenario Creator</kbd> in the sidebar. From here you can create
roads and vehicles using the mouse by clicking the buttons in the "Driving
Scenario Creator" menu. Add additional Blender objects as desired. Then export
everything together by clicking <kbd>Export driving scenario</kbd>. Choose a
**directory** for the export and confirm.

## How to run exported scenarios

First install [esmini](ttps://github.com/esmini/esmini/releases). Preferably to
`/opt/esmini` and then put `/opt/esmini/bin` it in your `PATH` environment
variable with an `export PATH=$PATH:/opt/esmini/bin` at the end of the
`~/.bashrc`.

With esmini available the exported scenario can be run with

    cd <export_directory>
    esmini --osc xosc/export.xosc --window 50 50 800 400

## License

The source code of this tool is distributed under the GPL version 3.0 license as
required for all Blender add-ons. Note, that this does not imply that the tool
can not be used in a commercial context. In fact, there is probably no issue
using it in the same way as you would use Blender itself, Linux or GCC since you
will probably not be modifying the source code and/or linking against it without
contributing back your changes.

Furthermore, if your enterprise has already reached a state where open source
software contribution is possible or your business has embraced open source
software long ago, your contributions and pull requests are welcome if they are
maintainable.

## Credits

Credits go to
- [pyoscx/scenarigeneration](https://github.com/pyoscx/scenariogeneration)
  developers for the .xodr/.xosc generating/writing lib used as backend
- [Archipack](https://github.com/s-leger/archipack) add-on developer(s) for
  general Blender add-on tool inspiration
- Blender Add Curve: Extra Objects extension authors for inspiration on ring
  segments

## Main author/maintainer contact

Please open issues and pull requests on GitHub to discuss openly. For private
support inquiries contact the repository owner via email, Twitter or create an
issue to initiate the communication. If you consider contributing large new
features please consider to have a discussion before beginning with the clean
implementation.
