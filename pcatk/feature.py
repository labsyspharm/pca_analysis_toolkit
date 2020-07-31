import numpy as np
import skimage.measure as smeasure


def pixel2mask(image: np.ndarray, low: float, high: float) -> np.ndarray:
    """
    Binarize pixel intensities. Pixels with intensity higher than the lower
    bound and also connected to at least one pixel of intensity higher than
    higher bound will be labeled True, otherwise False.

    Args:
        image: np.ndarray
            Intensity image.
        low: float
            Lower bound.
        high: float
            Higher bound.

    Return: np.ndarray of type bool
    """
    mask = image > low
    labels = smeasure.label(mask, background=0)
    for region in smeasure.regionprops(label_image=labels, intensity_image=image):
        if region.max_intensity < high:
            mask[region.coords[:, 0], region.coords[:, 1]] = 0

    return mask
