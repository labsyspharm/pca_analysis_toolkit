# PCA analysis toolkit

Analysis toolkit for the Pre-Cancer Atlas project. This toolkit is meant for exploratory analyses that changes rapidly. 

Images, mostly acquired through the [CyCIF technology](https://www.cycif.org/), are assumed to be processed first by [mcmicro-nf](https://github.com/labsyspharm/mcmicro-nf), where most of the heavy computation for illumination correction, stitching, registration, nuclei & cell segmentation, and feature quantification are done. The images are then passed to this toolkit for rapid iterations of exploratory analyses.

## Installation
Currently only support `pip`:
```
pip install pcatk
```

## Modules
* `convert`  
   Unpack and repack ome.tif files to TIFF images.
* `exemplar`  
   Sample, render, and assemble single cell images.
* `feature`  
   Pixel binarization as feature generation.
* `measure`  
   Mini-tile and region-wise Pearson correlation coefficient.
* `util`  
   Utility functions.
* `external`  
   Useful external code.
