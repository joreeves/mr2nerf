# %%

import numpy as np


inp1 = {
    "width": "2992",
    "height": "2000",
    "sensorWidth": "23.5",
    "sensorHeight": "15.708556175231934",
    "type": "radial3",
    "focalLength": "46.696858288770052"
}

inp2 = {
    "width": "3040",
    "height": "4056",
    "sensorWidth": "36",
    "sensorHeight": "26.982248306274414",
    "focalLength": "38.868769790279487",
    }

# %%

def build_sensor_test(inp):
    focal = float(inp['focalLength'])

    sensor_width = float(inp['sensorWidth'])
    sensor_height = float(inp['sensorHeight'])

    width = float(inp['width'])
    height = float(inp['height'])

    # angle_of_view_x = 2 * np.arctan(sensor_width / (2 * focal))
    # angle_of_view_y = 2 * np.arctan(sensor_height / (2 * focal))

    # fl_x = width / (2 * np.tan(angle_of_view_x / 2))
    # fl_y = height / (2 * np.tan(angle_of_view_y / 2))

    fl_x = (width * focal) / sensor_width
    fl_y = (height * focal) / sensor_height

    return fl_x, fl_y

fl_x, fl_y = build_sensor_test(inp2)

print(fl_x, fl_y)


# %%

print(float(inp1['width']) / float(inp1['height']))
print(float(inp1['sensorWidth']) / float(inp1['sensorHeight']))

print(float(inp2['width']) / float(inp2['height']))
print(float(inp2['sensorWidth']) / float(inp2['sensorHeight']))

print(np.isclose(float(inp1['width']) / float(inp1['height']), float(inp1['sensorWidth']) / float(inp1['sensorHeight'])))
print(np.isclose(float(inp2['width']) / float(inp2['height']), float(inp2['sensorWidth']) / float(inp2['sensorHeight'])))

# %%