# %%

import numpy as np
import json

# json_path = r"C:\Users\jreeves\Downloads\for_JSON\sfm_in-ext_only.json"
json_path = r"C:\Users\jreeves\Downloads\for_JSON\sfm_all.json"

with open(json_path, 'r') as f:
    data = json.load(f)

# %%

# for k,v in data.items():
#     dat = json.dumps(v[0], indent=4)
#     print(k, ',\n', dat, '\n\n')

# %%

poses = data['poses']  # Transforms
intrinsics = data['intrinsics']  # Camera intrinsics
views = data['views']
structure = data['structure']

# %%

pose_ids = [p['poseId'] for p in poses]
intrinsic_ids = [i['intrinsicId'] for i in intrinsics]

# %% CHECK TRANSFORM

pose = poses[0]['pose']

transform = pose['transform']
rotation = transform['rotation']
center = transform['center']

M = np.eye(4)
M[:3,:3] = np.array(rotation).reshape(3,3)
M[:3,3] = np.array(center)

# %%

from pytransform3d.rotations import check_matrix

total = np.eye(3)

for pose in poses:
    xfrm = pose['pose']['transform']
    rot = np.asarray(xfrm['rotation'])
    rot = rot.reshape(3,3).astype(float)

    total += np.abs(rot)

    M = np.eye(3)
    M = rot
    # M[:2, :3] = rot[1:3, :3]
    # M[2, :3] = rot[0, :3]

    try:
        ret = check_matrix(M)
    except ValueError as e:
        print(e, '\n')

    print(np.round(M, 4), '\n')

print(total / len(poses))

# %% CHECK INTRINSICS

import math

intrinsic = intrinsics[0]


def build_sensor(intrinsic):
    out = {}
    out["w"] = intrinsic['width']
    out["h"] = intrinsic['height']
    out["fl_x"] = intrinsic['focalLength']
    out["fl_y"] = intrinsic['focalLength']

    # # Given the w, h, pixel_width, pixel_height, and focal_length
    # # Calculate the focal length in pixels
    # fl_pxl = (w * focal_length) / (w * pixel_width)

    camera_angle_x = math.atan(float(out["w"]) / (float(intrinsic['focalLength']) * 2)) * 2
    camera_angle_y = math.atan(float(out["h"]) / (float(intrinsic['focalLength']) * 2)) * 2

    out["camera_angle_x"] = camera_angle_x
    out["camera_angle_y"] = camera_angle_y

    out["cx"] = intrinsic['principalPoint'][0]
    out["cy"] = intrinsic['principalPoint'][1]

    if intrinsic['type'] == 'radial3':
        for i, coef in enumerate(intrinsic['distortionParams']):
            out["k{}".format(i)] = coef

    # intrinsics_keys = ['cx', 'cy', 'b1', 'b2',
    #                    'k1', 'k2', 'k3', 'k4',
    #                    'p1', 'p2', 'p3', 'p4']
    
    return out

build_sensor(intrinsic)

# %% CHECK VIEWS

from pathlib import Path

view = views[0]

# Get poseId
poseId = view['poseId']

# Get intrinsicId
intrinsicId = view['intrinsicId']

# Path to image
path = Path(view['path'])


# %% CHECK STRUCTURE