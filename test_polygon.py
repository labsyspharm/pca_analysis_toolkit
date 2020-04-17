import os

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt
from skimage import draw, segmentation
from skimage.external import tifffile

if __name__ == '__main__':
    # path
    input_folderpath = os.path.expanduser('~/polygon_qc/input_data')
    roi_filepath = os.path.join(input_folderpath,
            'ZM131_5B_136_roi_0.ome.tif-1105078-rois.csv')
    image_filepath = os.path.join(input_folderpath,
            'ZM131_5B_136_roi_0.ome.tif')

    # get bounding box
    roi_df = pd.read_csv(roi_filepath)
    point_string = roi_df['all_points'].tolist()[0]
    point_list = [(float(p.split(',')[0]), float(p.split(',')[1]))\
            for p in point_string.split(' ')]
    bxl = min([p[0] for p in point_list])
    bxu = max([p[0] for p in point_list])
    byl = min([p[1] for p in point_list])
    byu = max([p[1] for p in point_list])
    bbox = (bxl, bxu), (byl, byu)
    
    # get ROI contour
    with tifffile.TiffFile(image_filepath) as tif_file:
        img_shape = tif_file.series[0].pages[0].shape

    rr, cc = draw.polygon(r=[p[0] for p in point_list], c=[p[1] for p in point_list],
            shape=img_shape)
    mask = np.zeros(img_shape)
    mask[rr, cc] = 1
    contour = segmentation.find_boundaries(mask, mode='inner')
    
    # check result
    plt.imshow(contour, cmap='gray')
    plt.show()
