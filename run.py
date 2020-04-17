import os
import sys
import shutil
import yaml

import numpy as np

from skimage import io, transform
from skimage.external import tifffile

import ashlar_pyramid

def crop(image, coord_dict):
    x_start = int(coord_dict['center_x'] - coord_dict['height']/2)
    x_end = x_start + coord_dict['height']
    y_start = int(coord_dict['center_y'] - coord_dict['width']/2)
    y_end = y_start + coord_dict['width']
    return image[y_start:y_end, x_start:x_end]

def dna_corrcoef(image_filepath, output_filepath):
    # open ome.tif image
    with tifffile.TiffFile(image_filepath) as infile:
        # get number of cycles, assuming 4 channels per cycle
        num_cycle = len(infile.series[0].pages) // 4
        # empty array to store correlation coefficient result
        corrcoef = np.zeros(num_cycle)
        # reference DNA intensity, hard-coded to be the DNA channel of the first cycle
        reference_dna = infile.series[0].pages[0].asarray(memmap=True)
        # loop over each cycle
        for cycle_index in range(num_cycle):
            # get the current DNA intensity
            current_dna = infile.series[0].pages[cycle_index*4].asarray(memmap=True)
            # calculate correlation coefficient. value range: [-1,+1]
            corrcoef[cycle_index] = np.corrcoef(current_dna.flatten(), reference_dna.flatten())[0,1]

    # write output file
    with open(output_filepath, 'w') as outfile:
        # write header
        outfile.write('cycle,reference_cycle,corrcoef\n')
        # loop over each cycle
        for cycle_index in range(num_cycle):
            # format output in CSV (comma separated) format
            output_string = '{},{},{}\n'.format(cycle_index+1, 1, corrcoef[cycle_index])
            # write to file
            outfile.write(output_string)

def process_single_image(param_dict):
    # unpack
    roi_df = pd.read_csv(params_dict['roi_filepath'])
    marker_list = pd.read_csv(param_dict['markers_filepath'], header=None)[0].tolist()
    mask_name_list = [name for name in param_dict if name.startswith('mask_')]

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

    def iter_array(bbox_coords=None):
        for array in itertools.chain(iter_channel(), iter_mask()):
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
        xl, xu, yl, yu = min(x_list), max(x_list), min(y_list), max(y_list)

        # crop image
        with tifffile.TiffFile(params[image_name]['image_filepath']) as infile:
            for channel_index, page in enumerate(infile.series[0].pages):
                channel = page.asarray(memmap=True)
                roi = crop(image=channel, coord_dict=params[image_name][roi_name])
                output_filepath = os.path.join(temp_folderpath, 'layer_{}.tif'.format(channel_index))
                filepath_list.append(output_filepath)
                # save file in ASHLAR-compatible way for later pyramid generation
                if channel_index == 0:
                    extra_arg = {'description': '!!xml!!'}
                else:
                    extra_arg = {'append': True}
                io.imsave(output_filepath, roi, metadata=None, bigtiff=True,
                        photometric='minisblack', **extra_arg)
        # crop masks
        for mask_name in mask_name_list:
            with tifffile.TiffFile(params[image_name][mask_name]['mask_filepath']) as infile:
                mask = infile.series[0].asarray(memmap=True)
                # handle data type
                mask = mask.astype(np.uint16) * np.iinfo(np.uint16).max
                if len(mask.shape) > 2:
                    # for Ring method of the segmenter, the nuclei intensity will
                    # be appended as the second layer, in the shape (C,X,Y)
                    mask = mask[0, ...]
                roi = crop(image=mask, coord_dict=params[image_name][roi_name])
                output_filepath = os.path.join(temp_folderpath,
                        'mask_{}.tif'.format(mask_name[len('mask_'):]))
                filepath_list.append(output_filepath)
                marker_list.append(mask_name)
                # save file in ASHLAR-compatible way for later pyramid generation
                extra_arg = {'append': True}
                io.imsave(output_filepath, roi, metadata=None, bigtiff=True,
                        photometric='minisblack', **extra_arg)
        # generate pyramid
        output_filepath = os.path.join(output_folderpath,
                '{}_roi_{}.ome.tif'.format(image_name[len('image_'):], roi_name[len('roi_'):]))
        ashlar_pyramid_hdf5.main(
            input_filepath_list=filepath_list,
            output_filepath=output_filepath,
            channel_name_list=marker_list,
            )
        # calculate DNA correlation coefficient
        input_filepath = os.path.join(output_folderpath,
                '{}_roi_{}.ome.tif'.format(image_name[len('image_'):], roi_name[len('roi_'):]))
        output_filepath = os.path.join(output_folderpath,
                '{}_roi_{}_corrcoef.csv'.format(image_name[len('image_'):], roi_name[len('roi_'):]))
        dna_corrcoef(image_filepath=input_filepath, output_filepath=output_filepath)
        # cleanup
        shutil.rmtree(temp_folderpath)
        print('Done image {} roi {}'.format(image_name[len('image_'):], roi_name[len('roi_'):]))

if __name__ == '__main__':
    # paths
    params_filepath = './params.yaml'
    output_folderpath = './'

    # load parameters
    with open(params_filepath, 'r') as infile:
        params = yaml.load(infile, Loader=yaml.Loader)

    # loop over images
    image_name_list = [name for name in params if name.startswith('image_')]
    for image_name in image_name_list:
        process_single_image(params[image_name])
