# blender-autotest

This utility intended to automatically run multiple
versions of [blender](https://github.com/blender/blender)
and render some models for benchmarking purpose.

Runnable files list:
* [`autotest.py`](autotest.py) - Run tests, collects logs in `/log` folder
  and produce results in `/out` folder: `.csv`, `.log` files and `.zip`
  archive collecting all this stuff together.
* [`analyzer.py`](analyzer.py) - Parse existing log files from `/log` folder
  and generate summary `.csv` file in `/out` folder
* [`plotter.py`](plotter.py) - Parse summary `.csv` files from `/out` folder
  draw some diagrams and store it in `.png` files next to them

For testing you need just pure python without any dependencies.
Given [`requirements.txt`](requirements.txt) suitable only for plotting.
