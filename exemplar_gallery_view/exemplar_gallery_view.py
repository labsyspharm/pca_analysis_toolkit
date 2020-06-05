import os
import sys

import numpy as np

from skimage.external import tifffile
from skimage import io, measure, segmentation, img_as_float
from matplotlib import pyplot as plt

def generate_cell(image_filepath, mask_filepath, channel_list, tile_shape,
        outline=False):
    mask = io.imread(mask_filepath)
    with tifffile.TiffFile(image_filepath) as infile:
        img_shape = infile.series[0].pages[0].shape

        for region in measure.regionprops(mask):
            # calculate tile coordinate
            c = region.centroids
            txl = int(np.round(c[0]-tile_shape[0]/2))
            tyl = int(np.round(c[1]-tile_shape[1]/2))
            txu, tyu = txl+tile_shape[0], tyl+tile_shape[1]

            # skip cells too close to image edge
            checklist = [txl >= 0, txu < img_shape[0], tyl >= 0, tyu < img_shape[1]]
            if not all(checklist):
                continue

            # compose
            cell = np.zeros( tile_shape + (len(channel_list),) )
            for channel in channel_list:
                img = infile.series[0].pages[channel].asarray(memmap=True)
                cell_img = img[txl:txu, tyl:tyu, channel]
                cell[..., channel] = img_as_float(cell_img)

            # add outline
            if outline:
                cm = mask[txl:txu, tyl:tyu].copy()
                co = segmentation.find_boundaries(cm, mode='inner')\
                        .astype(float)
                for ch in range(cell.shape[2]):
                    cell[..., ch] = np.maximum(cell[..., ch], co)

            yield cell

if __name__ == '__main__':
    # parameters
    # todo: move params to yaml file
    gallery_dim = (10, 10)
    tile_shape = (100, 100)
    channel_list = [0, 1, 2]

    fig, axes = plt.subplots(ncols=gallery_dim[0], nrows=gallery_dim[1],
            sharex=True, sharey=True)
    for ax, cell in zip(axes.flatten(), generate_cell(
        image_filepath=image_filepath,
        mask_filepath=mask_filepath,
        channel_list=channel_list,
        tile_shape=tile_shape,
        outline=True)):
        ax.imshow(cell)
        ax.set_xticks([])
        ax.set_yticks([])

    fig.tight_layout()
    plt.show()
