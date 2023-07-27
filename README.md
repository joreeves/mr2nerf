# Meshroom camera location to NERF conversion tool with per camera intrinsics
This tool is for use with https://github.com/NVlabs/instant-ngp and allows the use of Meshroom camera locations.

## Usage
In Meshroom, add a ConvertSfMFormat node and change the SfM Format to json.
![af32538a-bd34-4c62-aa1d-9706002ea0a0](https://github.com/joreeves/mr2nerf/assets/82180221/3663a596-fe07-4a40-9cd8-e78cb2ca593d)

Optional: Meshroom does not align or constrain solved cameras, you may want to add 
a SfMTransform after the StructureFromMotion node, set the Transformation Method to Manual,
and adjust the location and rotation of the solved cameras.

When you Start the Meshroom processing, it will generate a folder for the output of the
ConvertSfMFormat node, which you can easily find by right clicking on the node and
selecting Open Folder. The file sfm.json will be generated when Meshroom is done processing.
This is the file you need for this script's `--input` function.
![0eec4a33-97a7-4c38-91dd-5261500aae68](https://github.com/joreeves/mr2nerf/assets/82180221/1cd001b8-7612-44f1-abe7-a4696a98a357)

Run the mr2nerf.py on this JSON file using the following command, replacing the text in brackets […] with the file names and paths on your machine:

## Commands
Example:
- Replace `[PATH_TO_JSON_FILE]` with the path to the JSON that was exported from Meshroom
- Replace `[PATH_TO_IMAGES]` with the path to your images folder
```
python mr2nerf.py --input "[PATH_TO_JSON_FILE].json" --imgfolder "[PATH_TO_IMAGES]"
```
The quotes are only required if you have spaces in any of the folder or file names.

## Additional command examples
Scale the scene up by 100
```
python mr2nerf.py --input "[NAME_OF_JSON_FILE].json" --imgfolder "[PATH_TO_IMAGES]" --scale 100
```

Display the cameras in 3d and set the camera size (for debugging only, requires installing `matplotlib` and `pytransform3d`)
```
python mr2nerf.py --input "[NAME_OF_JSON_FILE].json" --imgfolder "[PATH_TO_IMAGES]" --plot --camera_size 1
```

Arguments:

| Argument               | Default Value   | Description                                  |
|------------------------|-----------------|----------------------------------------------|
| --input                | None            | specify json file location                   |
| --out                  | transforms.json | specify output file path                     |
| --imgfolder            | .\images        | location of image folder                     |
| --imgtype              | jpg             | ex.: jpg, png, ...                           |
| --aabb_scale           | 16              | sets the aabb scale                          |
| --no_scene_orientation | False           | disable the Reality Capture orientation      |
| --no_scale             | False           | disable the Reality Capture scale            |
| --no_center            | False           | disable the scene centering                  |
| --plot                 | False           | display the camera positions                 |
| --camera_size          | 0.1             | the size of the displayed cameras            |
| --debug_ignore_images  | False           | ignores the input images, for debugging only |
| --threads              | 8               | number of threads to use when reading images |
