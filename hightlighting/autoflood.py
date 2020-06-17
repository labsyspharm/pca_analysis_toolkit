import argparse

import numpy as np
import tifffile
import scipy.ndimage

from skimage import io, segmentation, measure, exposure

def select_bbox(img, bbox):
    min_row, min_col, max_row, max_col = bbox
    return img[min_row:max_row, min_col:max_col]

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('in_filepath', type=str,
            help='File path of the input ome.tif image')
    parser.add_argument('channel_index', type=int,
            help='Channel in input ome.tif image, starts at zero')
    parser.add_argument('start_threshold', type=int,
            help='Threshold to seed with, in uint16 range')
    parser.add_argument('stop_threshold', type=int,
            help='Threshold to stop growth at, in uint16 range')
    parser.add_argument('out_filepath', type=str,
            help='File path of the output .tif mask')
    args = parser.parse_args()

    # load data
    with tifffile.TiffFile(args.in_filepath) as tif:
        img = tif.series[0].pages[args.channel_index].asarray()
    img_scaled = exposure.rescale_intensity(img,
            in_range=tuple(np.percentile(img, (1, 99))))
    mask = img_scaled > args.start_threshold

    start = img_scaled.max()
    stop = args.stop_threshold

    for threshold in range(start, stop, -1):
        # check if any step needed
        if (img_scaled[np.logical_not(mask)]==threshold).sum() == 0:
            continue
        repeat = True
        while repeat:
            mask_freeze = mask.copy()
            # region defined by the highlighting
            labeled_mask, _ = scipy.ndimage.label(mask)
            region_list = measure.regionprops(label_image=labeled_mask,
                    intensity_image=img_scaled)
            # small chunks for faster iteration
            for region in region_list:
                # slice
                min_row, min_col, max_row, max_col = region.bbox
                # expand bounding box
                w = 1
                min_row, min_col = max(min_row-w, 0), max(min_col-w, 0)
                max_row = min(max_row+w, mask.shape[0])
                max_col = min(max_col+w, mask.shape[1])
                # slice
                img_small = img_scaled[min_row:max_row, min_col:max_col]
                mask_small = mask[min_row:max_row, min_col:max_col]
                # check if any space (potential) to grow
                potential_small = img_small >= threshold
                if potential_small.sum() > 0:
                    # most compute-intensive step
                    boundary_small = segmentation.find_boundaries(mask_small,
                            mode='outer')
                    # step is reachable potential
                    step_small = np.logical_and(boundary_small, potential_small)
                    mask[min_row:max_row, min_col:max_col]\
                            = np.logical_or(mask_small, step_small)
            # check
            if np.array_equal(mask, mask_freeze):
                repeat = False
#                # keep growing until no further step available
#                while step_small.sum() > 0:
#                    # combine new and old pixels
#                    mask_small = np.logical_or(mask_small, step_small)
#                    # most compute-heavy step
#                    boundary_small = segmentation.find_boundaries(mask_small,
#                            mode='outer')
#                    # check step again using the new boundary
#                    step_small = np.logical_and(boundary_small, potential_small)
#                # put back to big mask
#                mask[min_row:max_row, min_col:max_col] = mask_small

    # save
    io.imsave(args.out_filepath, mask)
