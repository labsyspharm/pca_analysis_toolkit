import typing

import numpy as np
import pandas as pd

from skimage.measure import regionprops

from external import blockwise_view


def minitile_corrcoef(
    arr1: np.ndarray,
    arr2: np.ndarray,
    block_shape: typing.Tuple[int, int],
    keep_shape: bool = False,
) -> np.ndarray:
    """
    Blockwise correlation coefficient.

    Args:
        arr1, arr2: np.ndarray
            Input images to compare.
        block_shape: tuple of int
            Shape of mini-tile.
        keep_shape: bool [optional]
            Keep same shape as input images or just one pixel per mini-tile.
            Default False.

    Return: correlation coefficient heatmap.
    """
    # make blocks
    b1 = blockwise_view(arr1, block_shape, require_aligned_blocks=False, aslist=False)
    b2 = blockwise_view(arr2, block_shape, require_aligned_blocks=False, aslist=False)
    # subtract mean
    axes = tuple(np.arange(b1.ndim, dtype=int)[b1.ndim // 2:])
    b1 -= b1.mean(axis=axes, keepdims=True)
    b2 -= b2.mean(axis=axes, keepdims=True)
    # numerator of corrcoef
    numerator = np.multiply(b1, b2).mean(axis=axes, keepdims=keep_shape)
    # denomenator of corrcoef
    dof = np.prod(b1.shape[slice(axes[0], axes[-1] + 1)])
    b1_std = np.sqrt((b1 ** 2).mean(axis=axes, keepdims=keep_shape) / dof)
    b2_std = np.sqrt((b2 ** 2).mean(axis=axes, keepdims=keep_shape) / dof)
    denominator = np.multiply(b1_std, b2_std)
    # divide
    out = np.divide(numerator, denominator)

    return out


def region_corrcoef(
    arr1: np.ndarray, arr2: np.ndarray, mask: np.ndarray, return_dataframe: bool = True
) -> typing.Union[np.ndarray, pd.DataFrame]:
    """
    Region-wise correlation coefficient.

    Args:
        arr1, arr2: np.ndarray
            Input images to compare.
        mask: np.ndarray
            Mask of integer defining regions.
        return_dataframe: bool [optional]
            If True, return dataframe of region label and correlation
            coefficients, else return an array with same shape as input.
            Default True.
    """
    # if memory usage is an issue here, pass dask.array as input
    # and use dask_image.ndmeasure.labeled_comprehension
    coef_dict = {}
    for region in regionprops(mask):
        pix1 = arr1[region.coords[:, 0], region.coords[:, 1]]
        pix2 = arr2[region.coords[:, 0], region.coords[:, 1]]
        coef_dict[region.label] = np.corrcoef(pix1, pix2)[0, 1]

    if return_dataframe:
        df = pd.DataFrame.from_records(
            list(coef_dict.items()), columns=["label", "corrcoef"]
        )
        return df
    else:
        coef_dict[0] = 0.0
        coef_image = np.vectorize(lambda x: coef_dict[x])(mask)
        return coef_image
