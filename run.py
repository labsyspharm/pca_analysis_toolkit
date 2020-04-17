import os
import yaml
import itertools

import numpy as np
import pandas as pd

from skimage.external import tifffile

import ashlar_pyramid

def dna_corrcoef(array_list, output_filepath):
    # calculate
    record = []
    ref = array_list[0]
    for ch in range(0, len(array_list), 4):
        cc = np.corrcoef(ref.flatten(), array_list[ch].flatten())[0, 1]
        record.append((ch+1, 1, cc))

    # write output file
    df = pd.DataFrame.from_records(record,
            columns=['cycle', 'reference_cycle', 'corrcoef'])
    df.to_csv(output_filepath, index=False)

def process_single_image(param_dict):
    # unpack
    roi_df = pd.read_csv(params_dict['roi_filepath'])
    marker_list = pd.read_csv(param_dict['markers_filepath'], header=None)[0].tolist()
    mask_name_list = [name[len('mask_'):] for name in param_dict\
            if name.startswith('mask_')]

    # make single-channel image iterator
    def iter_channel():
        with tifffile.TiffFile(param_dict['image_filepath']) as infile:
            for channel_index, page in enumerate(infile.series[0].pages):
                yield page.asarray(memmap=True)

    def iter_mask():
        for key in param_dict.keys():
            if key.startswith('mask_'):
                with tifffile.TiffFile(param_dict[key]['filepath']) as infile:
                    yield infile.series[0].asarray(memmap=True)

    def iter_roi(array_list, bbox_coords=None):
        for array in array_list:
            if bbox_coords is None:
                yield array
            else:
                xl, xu, yl, yu = bbox_coords
                yield array[xl:xu, yl:yu]

    # loop over ROIs
    for index, row in roi_df.iterrows():
        # parse points
        x_list = [float(t.split(',')[0]) for t in row['all_points'].split()]
        y_list = [float(t.split(',')[1]) for t in row['all_points'].split()]
        bbox_coords = min(x_list), max(x_list), min(y_list), max(y_list)

        # generate pyramid
        ashlar_pyramid.main(
                array_list=iter_roi(
                    array_list=itertools.chain(iter_channel(), iter_mask()),
                    bbox_coords),
                channel_name_list=marker_list + mask_name_list,
                out_path=param_dict['output_filepath'],
                )

        # calculate DNA correlation coefficient
        dna_corrcoef(
                array_list=list(iter_roi(array_list=list(iter_channel()), bbox_coords)),
                output_filepath=param_dict['corrcoef_filepath'],
                )

if __name__ == '__main__':
    # paths
    params_filepath = './params.yaml'
    output_folderpath = './'

    # load parameters
    with open(params_filepath, 'r') as infile:
        param_dict = yaml.load(infile, Loader=yaml.Loader)

    # loop over images
    image_name_list = [name for name in params if name.startswith('image_')]
    for key in param_dict.keys():
        if key.startswith('image_'):
            process_single_image(param_dict[key])
