import os
import sys
import multiprocessing as mp
import itertools
import typing
import argparse

import numpy as np

from skimage import io, img_as_uint
from skimage.external import tifffile

def get_tile_coord(img_shape: typing.Tuple[int, int],
        tile_shape: typing.Tuple[int, int],
        ) -> typing.Iterable[typing.Tuple[typing.Tuple[int, int],
            typing.Tuple[int, int]]]:
    '''
    Generate tile coordinates of a given shape.

    Arg:
        img_shape: tuple[int, int]
            Shape of the 2D image.
        tile_shape: tupple[int, int]
            Shape of the 2D tile.

    Return
        Iterable of tile coordinates in
        ((x_start, x_end), (y_start, y_end)) format.
    '''
    dim_list = []
    for img_d, tile_d in zip(img_shape, tile_shape):
        chunks = np.array_split(np.arange(img_d, dtype=int), round(img_d/tile_d))
        chunk_coords = [(c[0], c[-1]+1) for c in chunks]
        dim_list.append(chunk_coords)
    return itertools.product(*dim_list)

def job_iterator(img1, img2, tile_shape):
    for tile_coord in get_tile_coord(img1.shape, tile_shape):
        (x_start, x_end), (y_start, y_end) = tile_coord
        tile1 = img1[x_start:x_end, y_start:y_end]
        tile2 = img2[x_start:x_end, y_start:y_end]
        job = {'tile1': tile1, 'tile2': tile2, 'tile_coord': tile_coord}
        yield job

def job_executor(job):
    corrcoef = np.corrcoef(job['tile1'].flatten(), job['tile2'].flatten())[0, 1]
    output = {'corrcoef': corrcoef, 'tile_coord': job['tile_coord']}
    return output

def minitile_corrcoef(img1: np.ndarray, img2: np.ndarray,
        tile_shape: typing.Tuple[int, int], nproc: int=None) -> np.ndarray:
    '''
    Compute Pearson correlation coefficient of each mini-tiles.

    Arg:
        img1, img2: np.ndarray
            2D images to calculate correlation coefficients from.
        tile_shape: tuple[int, int]
            Shape of the 2D tile.
        nproc: int, default -1
            Number of multiprocesses to spawn simultaneously. Default to use all
            available processes.

    Return
        np.ndarray with the same shape of img1 and img2, with value being
        the correlation coefficients. Pixels within the same mini-tile will
        share the same correlation coefficient value.
    '''
    out_array = np.zeros_like(img1, dtype=float)
    with mp.Pool(processes=nproc) as worker_pool:
        for output in worker_pool.imap_unordered(job_executor,
                job_iterator(img1, img2, tile_shape)):
            (x_start, x_end), (y_start, y_end) = output['tile_coord']
            out_array[x_start:x_end, y_start:y_end] = output['corrcoef']
    return out_array

if __name__ == '__main__':
    # parse input
    parser = argparse.ArgumentParser()
    parser.add_argument('image_filepath', type=str,
            help='File path to the ome.tif image.')
    parser.add_argument('channel1', type=int,
            help='Channel number (starting with 1) to compare.')
    parser.add_argument('channel2', type=int,
            help='Channel number (starting with 1) to compare.')
    parser.add_argument('tile_height', type=int,
            help='Height (in pixels) of the mini-tile.')
    parser.add_argument('tile_width', type=int,
            help='Width (in pixels) of the mini-tile.')
    parser.add_argument('output_filepath', type=str,
            help='File path to the output tiff image.')
    parser.add_argument('-p', '--process', type=int, default=None,
            help='Maximum number of workers, default all available workers.')
    args = parser.parse_args()

    # load data
    with tifffile.TiffFile(args.image_filepath, 'r') as infile:
        img1 = infile.series[0].pages[args.channel1-1].asarray(memmap=True)
        img2 = infile.series[0].pages[args.channel2-1].asarray(memmap=True)
    tile_shape = (args.tile_height, args.tile_width)
    nproc = args.process

    # run
    corrcoef_array = minitile_corrcoef(img1, img2, tile_shape, nproc)

    # save resutl to disk
    output_filepath = args.output_filepath
    if not output_filepath.endswith('.tif'):
        output_filepath += '.tif'
    output_array = img_as_uint((corrcoef_array+1)/2)
    io.imsave(output_filepath, output_array)
