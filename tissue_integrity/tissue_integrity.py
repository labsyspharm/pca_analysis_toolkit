import os
import sys
import re

import numpy as np
import pandas as pd

from skimage.external import tifffile

def dna_corrcoef(image_filepath, marker_list, output_filepath):
    # parse markers
    dna_pattern = [
            'DNA\d+', # 'DNA' followed by one or more digits
            'DNA_\d+', # 'DNA' followed by one or more digits
            ]
    def is_dna(n):
        for p in dna_pattern:
            if re.fullmatch(pattern=p, string=n) is not None:
                return True
        return False

    dna_index = [i for i, name in enumerate(marker_list) if is_dna(name)]

    # calculate
    record = []
    ref_channel = 0
    with tifffile.TiffFile(image_filepath) as tif:
        ref_array = tif.series[0].pages[ref_channel]\
                .asarray(memmap=True)\
                .flatten()
        for cycle, channel in enumerate(dna_index):
            test_array = tif.series[0].pages[channel]\
                    .asarray(memmap=True)\
                    .flatten()
            cc = np.corrcoef(ref_array, test_array)[0, 1]
            record.append([cycle+1, channel+1, ref_channel+1, cc])

    # write output file
    df = pd.DataFrame.from_records(record,
            columns=['cycle', 'channel', 'reference_channel', 'corrcoef'])
    df.to_csv(output_filepath, index=False, na_rep='nan')

if __name__ == '__main__':
    # paths
    image_filepath = sys.argv[1]
    marker_filepath = sys.argv[2]
    output_folderpath = sys.argv[3]

    marker_list = pd.read_csv(marker_filepath, header=None)[0].tolist()

    # construct output file name
    b = os.path.basename(image_filepath)

    ext_list = ['.ome.tif', '.tiff', '.tif']
    ext_match = None
    for ext in ext_list:
        if b.endswith(ext):
            ext_match = ext
            break
    if ext_match is None:
        ext_match = os.path.splitext(b)[1]
    n = b[:-len(ext_match)]

    output_filepath = os.path.join(output_folderpath, '{}_DNACorrCoef.csv'.format(n))

    dna_corrcoef(
            image_filepath=image_filepath,
            marker_list=marker_list,
            output_filepath=output_filepath,
            )
