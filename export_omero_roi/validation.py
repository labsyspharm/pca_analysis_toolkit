import pandas as pd
import re
import skimage.io
from skimage.draw import polygon
import numpy as np


img = skimage.io.imread('16_c0.tif')
table = pd.read_csv('16.ome.tif-1207098-rois.csv')

all_points = [
    np.array(re.findall(r'\d+\.\d+', s))
        .astype(np.float64)
        .reshape(-1, 2)
    for s in table['all_points']
]

def find_bound(coors):
    # return [[x_min, ymin], [x_max, y_max]]
    return (
        coors.min(axis=0).astype(np.int64),
        coors.max(axis=0).astype(np.int64)
        )

bounds = [find_bound(i) for i in all_points]

def crop_roi(idx):
    points = all_points[idx]
    bound = bounds[idx]

    # Add 1 to upper bounds for subpixels
    roi = img[
        bound[0][1]:bound[1][1] + 1,
        bound[0][0]:bound[1][0] + 1
    ]

    mask = np.zeros_like(roi)
    rr, cc = polygon((points - bound[0])[..., 1], (points - bound[0])[..., 0])
    mask[rr, cc] = 1
    
    skimage.io.imsave(
        '{:03}-{}.tif'.format(idx + 1, table['Name'][idx]),
        roi * mask
    )

for i in range(len(table['Name'])):
    crop_roi(i)