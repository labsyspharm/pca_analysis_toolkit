import os
import sys
import glob
import multiprocessing as mp
import csv

import numpy as np
import pandas as pd
import tqdm

from skimage import io
from skimage.external import tifffile

def get_background_vector(cellmask_filepath, img_filepath):
    cellmask = io.imread(cellmask_filepath)
    background_index = np.argwhere(cellmask == 0)

    with tifffile.TiffFile(img_filepath) as tif:
        img = tif.series[0].asarray() # axis order: CXY
        
    img = img[:-1, ...] # last channel is ROI mask
    background = img[:, background_index[:, 0], background_index[:, 1]]
    background = background.T # axis order: NC
    background = background.astype(float) + 1e-12 # for numerical stability of log
    background = np.log10(background) # usually more gaussian-like in log space
    return np.median(background, axis=0)

def gen_job(parent_folderpath):
    name_list = os.listdir(parent_folderpath)
    for name in name_list:
        img_pattern = os.path.join(parent_folderpath, name, 'registration',
                '*.ome.tif')
        img_filepath = glob.glob(img_pattern)[0]

        cellmask_pattern = os.path.join(parent_folderpath, name, 'segmentation',
                name, 'cellRingMask.tif')
        cellmask_filepath = glob.glob(cellmask_pattern)[0]

        job = {'cellmask_filepath': cellmask_filepath,
                'img_filepath': img_filepath,
                }
        yield job

def run_job(job):
    name = os.path.basename(job['img_filepath'])[:-len('.ome.tif')]
    fields = name.split('_')
    slide_id = '{}_{}'.format(fields[0], fields[1])
    roi_row_id = fields[2]
    vec = get_background_vector(job['cellmask_filepath'], job['img_filepath'])
    return slide_id, roi_row_id, vec

if __name__ == '__main__':
    # paths
    ws_folderpath = '/n/scratch2/hw233/workspace_z170'
    parent_folderpath = os.path.join(ws_folderpath, 'mcmicro', 'done')
    marker_filepath = os.path.join(ws_folderpath, 'marker_files',
            'Z170_1_markers.csv')
    output_filepath = os.path.join(ws_folderpath, 'background_vector',
            'background_vectors.csv')

    # prepare parallelization
    n_proc = int(sys.argv[1])
    pool = mp.Pool(n_proc)

    # load data dimensions
    with open(marker_filepath, 'r') as f:
        marker_list = [line.strip() for line in f.readlines()]
    n_marker = len(marker_list)
    n_roi = len(os.listdir(parent_folderpath))

    # prepare containers
    outfile = open(output_filepath, 'w', newline='')
    outwriter = csv.writer(outfile, delimiter=',')
    outwriter.writerow(['slide_id', 'roi_row_id'] + marker_list)

    # main loop
    for slide_id, roi_row_id, vec in pool.imap_unordered(
        run_job, gen_job(parent_folderpath)):

        row = [slide_id, roi_row_id] + list(vec)
        outwriter.writerow(row)
        outfile.flush()

    outfile.close()
