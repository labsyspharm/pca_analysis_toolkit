import typing
from pathlib import Path

import numpy as np
import skimage.io as sio
import matplotlib.colors as mcolors

from skimage.measure import regionprops_table
from skimage import img_as_float, img_as_ubyte

from pcatk import util


Slice = typing.Tuple[slice, slice]


def sample(
    mask: np.ndarray, tile_size: typing.Tuple[int, int], size: int
) -> typing.Dict[int, Slice]:
    """
    Sample cells.

    Args:
        mask: np.ndarray
            Mask image for skimage.feature.regionprops
        tile_size: tuple of int
            Crop size for individual cells.
        size: int
            Sample size.

    Return: dict of label -> tuple of slice objects
    """
    # filter out cells at boundary
    props = regionprops_table(mask, properties=["label", "centroid"])
    mask = (
        (props["centroid-0"] > tile_size[0])
        & (props["centroid-0"] < mask.shape[0] - tile_size[0])
        & (props["centroid-1"] > tile_size[1])
        & (props["centroid-1"] < mask.shape[1] - tile_size[1])
    )
    for key in props:
        props[key] = props[key][mask]
    # sampling
    count = props["label"].shape[0]
    index = np.random.choice(range(count), size=size, replace=False)
    for key in props:
        props[key] = props[key][index]
    # make slice output
    xl = np.rint(props["centroid-0"] - tile_size[0] // 2).astype(int)
    yl = np.rint(props["centroid-1"] - tile_size[1] // 2).astype(int)
    xu, yu = xl + tile_size[0], yl + tile_size[1]
    out_dict = {
        props["label"][i]: (slice(xl[i], xu[i]), slice(yl[i], yu[i]))
        for i in range(size)
    }

    return out_dict


def project2rgb(image: np.ndarray, color: str) -> np.ndarray:
    """
    Project an image from matplotlib.colors named color to RGB space.

    Args:
        image: np.ndarray
            Input 2-D image of shape (N, M).
        color: str
            matplotlib.colors named color.

    Return: np.ndarray of shape (N, M, 3)
    """
    out = color.gray2rgb(img_as_float(image))
    rgb_code = mcolors.to_rgb(color)

    return out * np.array(rgb_code)


def render(
    slice_dict: typing.Dict[int, Slice],
    image_dict: typing.Dict[str, np.ndarray],
    out_folderpath: str,
    overwrite: bool = True,
):
    """
    Render sampled cells.

    Args:
        slice_dict: dict of integer --> tuple of slice object.
            Output of sample function.
        image_dict: dict of str --> np.ndarray
            Key is matplotlib named color. Value is image as np.ndarray.
        out_folderpath: str
            Folder to save rendered figures.
        overwrite: bool [optional]
            Overwrite flag, default True.
    """
    # preprocessing
    out_folderpath = Path(out_folderpath)
    util.check_overwrite(overwrite=overwrite, path=out_folderpath)

    # not much memory optimization done for now
    # if memory is an issue, pass h5py.Dataset instead of np.ndarray
    # code below is compatible with h5py.Dataset
    for key in slice_dict:
        arr = np.stack(
            [project2rgb(image, color) for color, image in image_dict.items()], axis=0
        )
        arr = arr.max(axis=0)
        arr = img_as_ubyte(arr)
        out_filepath = out_folderpath / f"{key}.png"
        sio.imsave(out_filepath, arr)


def assemble(
    in_folderpath: str,
    out_filepath: str,
    shape: typing.Tuple[int, int],
    pad_width: int = None,
    overwrite: bool = True,
):
    """
    Assemble images into exemplar, supports padding.

    Args:
        in_folderpath: str
            Folder path of input images.
        out_filepath: str
            Output image path.
        shape: tuple of int
            Mosaic shape, ex. (10, 10).
        pad_width: int [optional]
            Padding as border. If None, no padding. Default None.
        overwrite: bool [optional]
            Overwrite flag, default True.
    """
    # preprocessing
    in_folderpath = Path(in_folderpath)
    out_filepath = Path(out_filepath)
    util.check_overwrite(out_filepath)

    # if fewer image than needed, add blank images
    image_list = [sio.imread(p) for p in in_folderpath.iterdir()]
    num_block = np.prod(shape)
    if len(image_list) < num_block:
        image_list.extend(
            [np.ones_like(image_list[0]) for _ in range(num_block - len(image_list))]
        )

    # add padding
    if pad_width is not None:
        image_list = [
            np.pad(
                image,
                pad_width=(pad_width, pad_width, 0),
                mode="constant",
                constant_values=1,
            )
            for image in image_list
        ]

    # assembling
    image_list = [image_list[i:i + shape[0]] for i in range(0, num_block, shape[0])]
    out = np.block(image_list)
    sio.imsave(out_filepath, out)
