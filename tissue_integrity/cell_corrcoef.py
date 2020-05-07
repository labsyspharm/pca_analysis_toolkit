import os
import re

import numpy as np
import pandas as pd

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
    c3_df = pd.DataFrame(np.nan, columns=['DNA{}_vs_1'.format(i) for i in dna_cycle]\
            + ['DNA{}_vs_prev'.format(i) for i in dna_cycle],
            index=range(feat_df.shape[0]))
    for col in ['CellId', 'X_position', 'Y_position']:
        c3_df[col] = feat_df[col].values

    # calculate corr coef
    test = []
    with tifffile.TiffFile(image_filepath) as tif:
        dna_image = np.stack([tif.series[0].pages[i].asarray(memmap=True)\
                for i in dna_index], axis=-1)

        for index, row in c3_df.iterrows():
            y, x = int(np.round(row['X_position'])), int(np.round(row['Y_position']))
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

