import logging
import logging.config

logging.config.dictConfig({
	'version': 1,
	'formatters': {
		'console': {
			'format': '%(asctime)s | %(levelname)s | %(filename)s : %(lineno)s | >>> %(message)s',
			'datefmt': '%Y-%m-%d %H:%M:%S'
		},
		'file': {
			'format': '%(asctime)s | %(levelname)s | %(filename)s : %(lineno)s | >>> %(message)s',
			'datefmt': '%Y-%m-%d %H:%M:%S'
		}
	},
	'handlers': {
		'console': {
			'class': 'logging.StreamHandler',
			'formatter': 'console',
			'level': 'INFO',
			'stream': 'ext://sys.stdout'
		},
		'file': {
			'class': 'logging.handlers.RotatingFileHandler',
			'formatter': 'file',
			'level': 'DEBUG',
			'filename': 'mr2nerf.log',
			'mode': 'a',
			'maxBytes': 0,
			'backupCount': 3
		}
	},
	'loggers': {
		'': {
			'handlers': ['console', 'file'],
			'level': 'DEBUG',
			'propagate': True
		}
	}
})

LOGGER = logging.getLogger(__name__)

import argparse
import csv
import json
import math
import numpy as np
import os
import cv2
from copy import deepcopy as dc

from tqdm import tqdm
from pathlib import Path

from utils import sharpness, Mat2Nerf, central_point, plot, _PLT, reflect
# from mat_utils import matrix_from_euler

from concurrent.futures import ThreadPoolExecutor


ROT_MAT = np.array([[1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0,-1, 0, 0],
                    [0, 0, 0, 1]])

def parse_args():
    parser = argparse.ArgumentParser(description="convert Reality Capture csv export to nerf format transforms.json")

    parser.add_argument("--input", help="specify json file location") #TODO: Chang to positional argument
    parser.add_argument("--out", dest="path", default="transforms.json", help="output path")
    parser.add_argument("--imgfolder", default="./images/", help="location of folder with images")
    parser.add_argument("--imgtype", default="jpg", help="type of images (ex. jpg, png, ...)")
    parser.add_argument("--aabb_scale", default=16, type=int, help="size of the aabb, default is 16")
    parser.add_argument("--plot", action="store_true", help="plot the cameras and the bounding region in 3D")
    parser.add_argument("--scale", default=1.0, type=float, help="scale the scene by a factor")
    parser.add_argument("--no_scale", action="store_true", help="DISABLES the scaling of the cameras to the bounding region")
    parser.add_argument("--no_center", action="store_true", help="DISABLES the centering of the cameras around the computed central point")
    parser.add_argument("--camera_size", default=0.2, type=float, help="size of the camera in the 3D plot. Does not affect the output.")
    parser.add_argument("--debug", action="store_true", help="enables debug mode")

    parser.add_argument("--debug_ignore_images", action="store_true", help="IGNORES the images in the xml file. For debugging purposes only.")

    parser.add_argument("--threads", default=8, type=int, help="number of threads to use for processing")

    args = parser.parse_args()
    return args


def build_sensor(intrinsic):
    out = {}
    out["w"] = float(intrinsic['width'])
    out["h"] = float(intrinsic['height'])

    # Focal length in mm
    focal = float(intrinsic['focalLength'])
    
    # Sensor width in mm
    sensor_width = float(intrinsic['sensorWidth'])
    sensor_height = float(intrinsic['sensorHeight'])

    # Focal length in pixels
    out["fl_x"] = (out["w"] * focal) / sensor_width
    out["fl_y"] = (out["h"] * focal) / sensor_height

    # out["fl_x"] = focal
    # out["fl_y"] = focal

    # # Given the w, h, pixel_width, pixel_height, and focal_length
    # # Calculate the focal length in pixels
    # fl_pxl = (w * focal_length) / (w * pixel_width)

    camera_angle_x = math.atan(out["w"] / (out['fl_x']) * 2) * 2
    camera_angle_y = math.atan(out["h"] / (out['fl_y']) * 2) * 2

    out["camera_angle_x"] = camera_angle_x
    out["camera_angle_y"] = camera_angle_y

    out["cx"] = float(intrinsic['principalPoint'][0]) + (out["w"] / 2.0)
    out["cy"] = float(intrinsic['principalPoint'][1]) + (out["h"] / 2.0)

    if intrinsic['type'] == 'radial3':
        for i, coef in enumerate(intrinsic['distortionParams']):
            out["k{}".format(i + 1)] = float(coef)

    # intrinsics_keys = ['cx', 'cy', 'b1', 'b2',
    #                    'k1', 'k2', 'k3', 'k4',
    #                    'p1', 'p2', 'p3', 'p4']
    
    return out


def init_logging(args):
	# Get handlers from logging config
	handlers = logging.getLogger().handlers

	if args.debug:
		for log in handlers:
			log.setLevel(logging.DEBUG)

	# Get log path from config
	log_path = Path(handlers[1].baseFilename)

	if log_path.is_file():
		handlers[1].doRollover()


if __name__ == "__main__":
    args = parse_args()

    init_logging(args)

    IMGFOLDER = Path(args.imgfolder)
    files = list(IMGFOLDER.glob('*.{}'.format(args.imgtype)))
    stems = list([f.stem for f in files])

    # Check if the files path has images in it
    if(len(files)==0) & (args.debug_ignore_images==False):
        LOGGER.error('No images found in folder: {}'.format(IMGFOLDER))
        exit()

    out = dict()
    out['aabb_scale'] = args.aabb_scale

    def read_img(cam):
        if args.debug_ignore_images:
            return cam, None
        img = cv2.imread(str(cam['file_path']))
        return cam, img

    frames = []

    with open(args.input, 'r') as f:
        data = json.load(f)

    transforms = {}
    for pose in data['poses']:
        transform = pose['pose']['transform']
        rot = np.asarray(transform['rotation'])
        rot = rot.reshape(3,3).astype(float)

        ctr = np.asarray(transform['center'])
        ctr = ctr.astype(float)

        M = np.eye(4)
        M[:3, :3] = rot
        M[:3, 3] = ctr * args.scale

        M = Mat2Nerf(M.astype(float))

        transforms[pose['poseId']] = np.dot(ROT_MAT, M)

    intrinsics = {}
    for intrinsic in data['intrinsics']:
        intrinsics[intrinsic['intrinsicId']] = build_sensor(intrinsic)

    frames = []
    for view in data['views']:
        # Path to image
        path = Path(view['path'])

        # Get the image name
        name = path.stem

        # Check if the image exists
        new_path = (IMGFOLDER / name).with_suffix(f'.{args.imgtype}')

        if (new_path not in files) or (new_path.exists() == False):
            LOGGER.warning(f'Image not found: {name}')
            continue

        # Get poseId
        poseId = view['poseId']

        # Get intrinsicId
        intrinsicId = view['intrinsicId']

        camera = {}
        camera.update(dc(intrinsics[intrinsicId]))
        camera['transform_matrix'] = transforms[poseId]
        camera['file_path'] = str(new_path)
        camera['ids'] = [poseId, intrinsicId]

        frames.append(camera)

    pbar = tqdm(total=len(frames), desc='Processing frames')
    with ThreadPoolExecutor(max_workers=args.threads) as exec:
         for i, (cam, img) in enumerate(exec.map(read_img, frames)):

            LOGGER.debug(f"Processing image: {cam['file_path']}")
            LOGGER.debug(f"PoseId {cam['ids'][0]} | IntrinsicId {cam['ids'][1]}")

            del cam['ids']

            cam['sharpness'] = 1 if args.debug_ignore_images else sharpness(img)

            LOGGER.debug(f"Camera {i:03d} info:")
            for k,v in camera.items():
                LOGGER.debug('{}: {}'.format(k, v))
            LOGGER.debug("Finished processing {i:03d}\n")

            pbar.update(1)

    out['frames'] = frames

    if args.no_center:
        center = np.zeros(3)
    else:
        # Compute the center of attention
        center = central_point(out)

    # Set the offset and convert to list
    for f in out["frames"]:
        f["transform_matrix"][0:3,3] -= center
        f["transform_matrix"] = f["transform_matrix"].tolist()

    with open(args.path, "w") as f:
        json.dump(out, f, indent=4)

    if _PLT & args.plot:
        plot(out, center, args.camera_size)