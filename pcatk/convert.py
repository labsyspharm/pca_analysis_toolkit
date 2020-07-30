import typing
import collections
from pathlib import Path

import h5py
import tifffile

from pcatk import util, ashlar_pyramid


def uniquify(name_list: typing.List[str]) -> typing.List[str]:
    """
    Uniquify names, a common issue in markers.csv files seen so far.

    Args:
        name_list: list of str
            Input names.

    Return: list of str, each being unique
    """
    count = collections.Counter(name_list)
    if count.most_common(1)[1] == 1:
        # most common name has frequency of one, meaning all names unique
        return name_list
    else:
        dup_count = {c[0]: 0 for c in count.most_common() if c[1] > 1}
        for i, name in enumerate(name_list):
            if name in dup_count:
                dup_count[name] += 1
                name_list[i] = f"{name}_{dup_count[name]}"
        return name_list


def name_generator(start: int = 0, step: int = 1):
    """
    Ever-increasing number generator.

    Args:
        start: int [optional]
            Starting number, default 0.
        step: int [optional]
            Increment, default 1.
    """
    x = start
    while True:
        yield str(x)
        x += step


def ometif2tif(
    in_filepath: str,
    out_folderpath: str,
    names_filepath: str = None,
    overwrite: bool = True,
):
    """
    Unpack ome.tif file into a folder of TIFF images.

    Args:
        in_filepath: str
            Input ome.tif file path.
        out_folderpath: str
            Output folder path.
        name_filepath: str [optional]
            Text file with each line the name of the channels.
        overwrite: bool [optional]
            Overwrite output folder if already exists. Default True.
    """
    # preprocessing
    in_filepath = Path(in_filepath)
    out_folderpath = Path(out_folderpath)
    names_filepath = Path(names_filepath)
    util.check_overwrite(overwrite=overwrite, path=out_folderpath)

    # load marker name
    if names_filepath is None:
        name_list = name_generator(start=1, step=1)
    else:
        name_list = names_filepath.read_text().splitlines()
        name_list = uniquify(name_list)

    # try to minimize memory usage here as each image can be several GB
    with tifffile.TiffFile(in_filepath) as tif:
        for name, pg in zip(name_list, tif.series[0].pages):
            out_filepath = out_folderpath / f"{name}.tif"
            tifffile.imsave(out_filepath, pg.asarray())


def ometif2hdf5(
    in_filepath: str,
    out_filepath: str,
    names_filepath: str = None,
    overwrite: bool = True,
):
    """
    Convert ome.tif file into HDF5 file.

    Args:
        in_filepath: str
            Input ome.tif file path.
        out_filepath: str
            Output .h5 file path.
        name_filepath: str [optional]
            Text file with each line the name of the channels. Default None.
            If None, as increasing numbers like 1, 2, 3, ...
        overwrite: bool [optional]
            Overwrite output folder if already exists. Default True.
    """
    # preprocessing
    in_filepath = Path(in_filepath)
    out_filepath = Path(out_filepath)
    names_filepath = Path(names_filepath)
    util.check_overwrite(overwrite=overwrite, path=out_filepath)

    # load marker name
    if names_filepath is None:
        name_list = name_generator(start=1, step=1)
    else:
        name_list = names_filepath.read_text().splitlines()
        name_list = uniquify(name_list)

    # automatic chunk size estimation
    with tifffile.TiffFile(in_filepath) as tif, h5py.File(out_filepath, "w") as out_f:
        for name, pg in zip(name_list, tif.series[0].pages):
            out_f.create_dataset(name=name, data=pg.asarray())


def tif2ometif(
    in_folderpath: str, out_filepath: str, tile_size: int = 1024, overwrite: bool = True
):
    """
    Concatenate channels and make pyramid.

    Args:
        in_folderpath: str
            Folder of input tif images.
        out_filepath: str
            Output ome.tif file path.
        tile_size: int [optional]
            Tile size lower cap for ashlar pyramid generator. Default 1024.
        overwrite: bool [optional]
            Overwrite flag, default True.
    """
    # preprocessing
    in_folderpath = Path(in_folderpath)
    out_filepath = Path(out_filepath)
    util.check_overwrite(overwrite=overwrite, path=out_filepath)

    # make generators
    def arr_gen():
        for x in in_folderpath.iterdir():
            yield tifffile.imread(x)

    def name_gen():
        for x in in_folderpath.iterdir():
            yield x.stem

    # pass to ashlar pyramid generator
    ashlar_pyramid.main(
        array_list=arr_gen(),
        channel_name_list=name_gen(),
        out_path=out_filepath,
        tile_size=tile_size,
    )
