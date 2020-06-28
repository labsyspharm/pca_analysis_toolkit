import argparse

import napari

from skimage import io
from napari import viewer as nv

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('in_filepath', type=str,
            help='File path of the input .tif image')
    parser.add_argument('threshold', type=int,
            help='Threshold for seeding, in uint16 range')
    args = parser.parse_args()

    img = io.imread(args.in_filepath)
    mask = img > args.threshold

    with napari.gui_qt():
        viewer = nv.Viewer()
        viewer.add_image(img, name='img')
        viewer.add_labels(mask, name='threshold')
        viewer.show()
