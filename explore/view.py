import typing
import argparse

import numpy as np
import napari
from napari import viewer as nv

from skimage import io, segmentation, img_as_uint, exposure
from skimage.external import tifffile

def view(img_filepath: str, marker_filepath: str, mask_filepath: str=None,
        selected_marker_list: typing.List[str]=None):
    '''
    Prepare napari viewer of (selected) channels of an ome.tif image.
    args:
        img_filepath: str
            File path of the ome.tif image.
        marker_filepath: str
            File path of the marker list, one line per marker name.
        mask_filepath: str [optional]
            File path of the cell (or nuclei) mask to include.
            If None, no mask will be included.
        selected_marker_list: list of str [optional]
            Specific markers to show. If not None, only show these markers.
            If None, show all markers in the marker list.
    '''
    # load data
    with open(marker_filepath, 'r') as infile:
        marker_list = [line.strip() for line in infile.readlines()]
    if mask_filepath is not None:
        mask = io.imread(mask_filepath)
        outline = segmentation.find_boundaries(mask>0, mode='inner')
        mask = img_as_uint(mask)
        outline = img_as_uint(outline)

    # check if selected markers exist
    if selected_marker_list is not None:
        tmp_list = []
        for name in selected_marker_list:
            if name in marker_list:
                tmp_list.append(name)
            else:
                print('selected marker {} not found in markers.csv'\
                        .format(name))
        selected_marker_list = tmp_list
    else:
        selected_marker_list = marker_list

    # load image to memory
    channel_list = []
    with tifffile.TiffFile(img_filepath) as infile:
        for name in selected_marker_list:
            index = marker_list.index(name)
            channel = infile.series[0].pages[index].asarray()
            channel_list.append((name, channel))

    # initialize napari session
    with napari.gui_qt():
        # create viewer
        viewer = nv.Viewer(show=False)

        # add layers
        for name, channel in channel_list:
            channel_adj = exposure.rescale_intensity(channel,
                    in_range=tuple(np.percentile(channel, (1, 99))))
            viewer.add_image(channel_adj, name=name, visible=False,
                    blending='additive')

        # turn on first 3 (or less) for display
        for cmap, layer in zip(['red', 'green', 'blue'], viewer.layers):
            layer.visible = True
            layer.colormap = cmap

        # add mask
        if mask_filepath is not None:
            viewer.add_labels(mask, name='mask', visible=False,
                    blending='additive')
            viewer.add_image(outline, name='outline', visible=True,
                    blending='additive', colormap='gray')

        viewer.show()

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('img_filepath', type=str,
            help='File path of the ome.tif image')
    parser.add_argument('marker_filepath', type=str,
            help='File path of the marker list')
    parser.add_argument('--mask_filepath', type=str, default=None,
            help='File path of the mask image')
    parser.add_argument('--markers', type=str, default=None,
            help='Selected marker names, separated by comma')
    args = parser.parse_args()

    # process
    if args.markers is None:
        selected_marker_list = args.markers
    else:
        selected_marker_list = args.markers.split(',')

    # run
    view(img_filepath=args.img_filepath,
            marker_filepath=args.marker_filepath,
            mask_filepath=args.mask_filepath,
            selected_marker_list=selected_marker_list,
            )
