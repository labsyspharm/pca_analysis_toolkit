import os
import sys
import glob

import numpy as np
import napari
from napari import viewer as nv

from skimage import io, segmentation, img_as_uint, exposure
from skimage.external import tifffile

if __name__ == '__main__':
    # paths
    roi_folderpath = sys.argv[1]
    roi_folderpath = os.path.expanduser(roi_folderpath)

    # parse path
    img_filepath = glob.glob(os.path.join(roi_folderpath, 'registration',
        '*.ome.tif'))[0]
    cellmask_filepath = glob.glob(os.path.join(roi_folderpath, 'segmentation',
        '*', 'cellRingMask.tif'))[0]
    marker_filepath = os.path.join(roi_folderpath, 'markers.csv')

    # load data
    with open(marker_filepath, 'r') as infile:
        marker_list = [line.strip() for line in infile.readlines()]
    cellmask = io.imread(cellmask_filepath)
    celloutline = segmentation.find_boundaries(cellmask>0, mode='inner')
    celloutline = img_as_uint(celloutline)

    # slice channels
    if len(sys.argv) > 2:
        selected_marker_list = []
        for name in sys.argv[2:]:
            if name in marker_list:
                selected_marker_list.append(name)
            else:
                print('specified marker {} not found in markers.csv'\
                        .format(name))
    else:
        selected_marker_list = marker_list
    channel_list = []
    with tifffile.TiffFile(img_filepath) as infile:
        for name in selected_marker_list:
            index = marker_list.index(name)
            channel = infile.series[0].pages[index].asarray()
            channel_list.append((name, channel))

    # initialize session
    with napari.gui_qt():
        # create viewer
        viewer = nv.Viewer(show=False)
        # add all channels
        for marker, channel in channel_list:
            img = exposure.rescale_intensity(channel,
                    in_range=tuple(np.percentile(channel, (1, 99))))
            viewer.add_image(img, name=marker, visible=False,
                    blending='additive')
        # add mask
        viewer.add_image(celloutline, name='celloutline', visible=False,
                blending='additive')
        # initial view
        if all(['DNA_'+str(i) in selected_marker_list for i in range(1, 4)]):
            config = {
                    'DNA_1': 'red',
                    'DNA_2': 'green',
                    'DNA_3': 'blue',
                    'celloutline': 'gray',
                    }
        else:
            config = {}
            for n, c in zip(selected_marker_list, ['red', 'green', 'blue']):
                config[n] = c
            config['celloutline'] = 'gray'
        # change visibility and colormap
        for key in config:
            viewer.layers[key].visible=True
            viewer.layers[key].colormap = config[key]

        viewer.show()
