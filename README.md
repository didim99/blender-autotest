# blender-autotest

This utility intended to automatically run multiple
versions of [blender](https://github.com/blender/blender)
and render some models for benchmarking purpose.

### Available functions

Runnable files list:
* [`autotest.py`](autotest.py) - Run tests, collects logs in `/log` folder
  and produce results in `/out` folder: `.csv`, `.log` files and `.zip`
  archive collecting all this stuff together.
* [`analyzer.py`](analyzer.py) - Parse existing log files from `/log` folder
  and generate summary `.csv` file in `/out` folder
* [`plotter.py`](plotter.py) - Parse summary `.csv` files from `/out` folder
  draw some diagrams and store it in `.png` files next to them

### Dependencies

For minimal testing you need just pure python without any dependencies.
Given [`requirements.txt`](requirements.txt) suitable if you want to get
CPU frequency statistics and hardware/OS information in output log.
[`requirements-plot.txt`](requirements-plot.txt) suitable for plotting.

### Running

Requirements:
* `python` command available from command line

Automation scripts:
* [`bootstrap`](scripts/) creates python virtual environment
  and installs all necessary dependencies for testing
* [`run-test`](scripts/) activates a virtual environment
  and starts testing script

Files named with `-direct` suffix provides support of
instant running (e.g. double-click in explorer). Files without that
suffix must be called from project's root folder via command line. 
