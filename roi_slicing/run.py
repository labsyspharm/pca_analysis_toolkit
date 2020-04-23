import os
import sys
import yaml
import itertools
import re

import numpy as np
import pandas as pd

from skimage import draw, segmentation
from skimage.external import tifffile

import ashlar_pyramid

def dna_corrcoef(array_list, marker_list, output_filepath):
    # parse markers
    dna_pattern = [
            'DNA\d+', # 'DNA' followed by one or more digits
            'DNA_\d+', # 'DNA' followed by one or more digits
            ]
    def is_dna(n):
        for p in dna_pattern:
            if re.fullmatch(pattern=p, string=n) is not None:
                return True
        return False

    dna_index = [i for i, name in enumerate(marker_list) if is_dna(name)]

    # calculate
    record = []
    ref_channel = 0
    for cycle, channel in enumerate(dna_index):
        cc = np.corrcoef(array_list[ref_channel].flatten(),
                array_list[channel].flatten())[0, 1]
        record.append([cycle+1, channel+1, ref_channel+1, cc])

    # write output file
    df = pd.DataFrame.from_records(record,
            columns=['cycle', 'channel', 'reference_channel', 'corrcoef'])
    df.to_csv(output_filepath, index=False, na_rep='nan')

def process_single_image(image_name, output_folderpath, param_dict):
    # unpack
    roi_df = pd.read_csv(param_dict['roi_filepath'])
    marker_list = pd.read_csv(param_dict['markers_filepath'], header=None)[0].tolist()

    with tifffile.TiffFile(param_dict['image_filepath']) as infile:
        img_shape = infile.series[0].pages[0].shape
        num_channel = len(infile.series[0].pages)

    # check if channels match
    if num_channel <= len(marker_list):
        marker_list = marker_list[:num_channel]
    else:
        print('image {} has more channels (n={}) than given markers (n={})'\
                ', skipped due to concern of incomplete data'\
                .format(image_name, num_channel, len(marker_list)))
        return

    # append mask and ROI to list
    mask_name_list = [name[len('mask_'):] for name in param_dict\
            if name.startswith('mask_')]
    name_list = marker_list + mask_name_list + ['ROI']

    # make single-channel image iterator
    def iter_channel():
        with tifffile.TiffFile(param_dict['image_filepath']) as infile:
            for channel_index, page in enumerate(infile.series[0].pages):
                yield page.asarray(memmap=True)

    def iter_mask():
        for key in param_dict.keys():
            if key.startswith('mask_'):
                with tifffile.TiffFile(param_dict[key]['filepath']) as infile:
                    yield infile.series[0].pages[0].asarray(memmap=True)[0, ...]

    def iter_roi(array_list, bbox_coords=None):
        for array in array_list:
            if bbox_coords is None:
                yield array
            else:
                b = [int(np.round(c)) for c in bbox_coords]
                yield array[b[0]:b[1], b[2]:b[3]]

    # loop over ROIs
    for index, row in roi_df.iterrows():
        # parse points
        y_list = [float(t.split(',')[0]) for t in row['all_points'].split()]
        x_list = [float(t.split(',')[1]) for t in row['all_points'].split()]
        bbox_coords = min(x_list), max(x_list), min(y_list), max(y_list)

        # check if bounding box is outside of image
        checklist = [bbox_coords[0] >= 0, bbox_coords[1] < img_shape[0],
                bbox_coords[2] >= 0, bbox_coords[3] < img_shape[1]]

        if not all(checklist):
            print('ROI {} has bounding box {} outside of image scope, skipped'\
                    .format(row['Name'], bbox_coords))
            continue

        # construct ROI mask
        rr, cc = draw.polygon(r=x_list, c=y_list, shape=img_shape)
        roi_mask = np.zeros(img_shape)
        roi_mask[rr, cc] = 1
        roi_contour = segmentation.find_boundaries(roi_mask, mode='inner')\
                .astype(np.uint16)

        # generate pyramid
        array_iterable = itertools.chain(iter_channel(), iter_mask(), [roi_contour])
        ashlar_pyramid.main(
                array_list=iter_roi(array_list=array_iterable, bbox_coords=bbox_coords),
                channel_name_list=name_list,
                out_path=os.path.join(output_folderpath,
                    '{}_{}.ome.tif'.format(image_name, row['Name'])),
                tile_size=32,
                )

        # calculate DNA correlation coefficient
        dna_corrcoef(
                array_list=list(iter_roi(array_list=list(iter_channel()),
                    bbox_coords=bbox_coords)),
                marker_list=marker_list,
                output_filepath=os.path.join(output_folderpath,
                    '{}_{}.csv'.format(image_name, row['Name'])),
                )

if __name__ == '__main__':
    # paths
    params_filepath = sys.argv[1]
    output_folderpath = sys.argv[2]

    # load parameters
    with open(params_filepath, 'r') as infile:
        param_dict = yaml.load(infile, Loader=yaml.Loader)

    # loop over images
    for key in param_dict.keys():
        if key.startswith('image_'):
            process_single_image(
                    image_name=key[len('image_'):],
                    output_folderpath=output_folderpath,
                    param_dict=param_dict[key],
                    )