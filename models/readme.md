Place your test models in `.blend` format to this folder.
Prepare separate models for CPU and GPU rendering (set
proper renderer engine, tile size, etc) and name models
with according suffix: `_cpu` or `_gpu`.

For GPU rendering specify the `CUDA` engine only, all
other engines will be tested automatically for blender
v2.91 and newer. For versions earlier than 2.91 we can't
override render engine via command line and test will be
run only with engine specified in `.blend` file.

For example, if your model named `RyzenGraphic_27.blend`
you should configure `RyzenGraphic_27_cpu.blend` and
`RyzenGraphic_27_gpu.blend` files and put into this folder.

Models that hasn't any suffix specified considering only
for CPU rendering.
