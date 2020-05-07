import os
import re

import numpy as np
import pandas as pd
import tqdm

from matplotlib import pyplot as plt
from skimage.external import tifffile
from skimage import io, measure

def is_DNA(name):
    patterns = ['DNA\d+', 'DNA_\d+']
    for p in patterns:
        if re.fullmatch(pattern=p, string=name) is not None:
            return True
    return False

def pairwise_corrcoef(arr1, arr2):
    numerator = np.multiply(arr1, arr2).sum(axis=1)
    denom1 = np.sqrt((arr1 ** 2).sum(axis=1))
    denom2 = np.sqrt((arr2 ** 2).sum(axis=1))
    denom = np.multiply(denom1, denom2)
    r = np.divide(numerator, denom)
    return r

def custom_corrcoef(array):
    '''
    Vectorized custom Pearson correlation coefficient.
    '''
    # pre-processing
    arr = array - array.mean(axis=1, keepdims=True)

    # vs DNA 1
    arr_ref = np.tile(arr[[0], :], (arr.shape[0], 1))
    r1 = pairwise_corrcoef(arr, arr_ref)

    # vs prev
    arr_prev = np.vstack([arr[[0], :], arr[0:-1, :]])
    rprev = pairwise_corrcoef(arr, arr_prev)

    return r1, rprev

if __name__ == '__main__':
    # paths
    data_folderpath = os.path.expanduser('~/cell_corrcoef/ZM131_10B_286_roi_A')
    feat_filepath = os.path.join(data_folderpath, 'feature_extraction',
            'ZM131_10B_286_roi_A.csv')
    cellmask_filepath = os.path.join(data_folderpath, 'segmentation',
            'cellRingMask.tif')
    image_filepath = os.path.join(data_folderpath, 'registration',
            'ZM131_10B_286_roi_A.ome.tif')
    marker_filepath = os.path.expanduser('~/cell_corrcoef/markers.csv')

    # load data
    feat_df = pd.read_csv(feat_filepath)
    cellmask = io.imread(cellmask_filepath)
    cellregion = {r.label: r for r in measure.regionprops(cellmask)}
    marker_list = pd.read_csv(marker_filepath, header=None)[0].tolist()

    # parse
    dna_index = [i for i, n in enumerate(marker_list) if is_DNA(n)]
    dna_cycle = list(range(1, len(dna_index)+1))
    cc1_col = ['DNA{}_vs_1'.format(i) for i in dna_cycle]
    ccprev_col = ['DNA{}_vs_prev'.format(i) for i in dna_cycle]

    # calculate corr coef
    record = []
    with tifffile.TiffFile(image_filepath) as tif:
        dna_image = np.stack([tif.series[0].pages[i].asarray(memmap=True)\
                for i in dna_index], axis=-1)

        for index in tqdm.tqdm(feat_df.index):
            cellid, xpos, ypos = feat_df.loc[index, ['CellId', 'Y_position', 'X_position']]
            x, y = int(np.round(xpos)), int(np.round(ypos))
            checklist = [x >= 0, x < cellmask.shape[0], y >= 0, y < cellmask.shape[1]]
            if not all(checklist):
                continue
            region_id = cellmask[x, y]
            if region_id == 0:
                continue
            region = cellregion[region_id]
            px_coords = region.coords
            px = dna_image[px_coords[:, 0], px_coords[:, 1], :].T
            r1, rprev = custom_corrcoef(px)

            # pack
            result = {'CellId': cellid, 'X_position': xpos, 'Y_position': ypos}
            for i in range(r1.shape[0]):
                result[cc1_col[i]] = r1[i]
            for i in range(rprev.shape[0]):
                result[ccprev_col[i]] = rprev[i]
            record.append(result)

    c3_df = pd.DataFrame.from_records(record)
    c3_df.to_csv('c3_df.csv', index=False, na_rep='NaN')
