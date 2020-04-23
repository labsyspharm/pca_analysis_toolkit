# PCA analysis toolkit

Analysis toolkit for the Pre-Cancer Atlas project. This toolkit is meant for exploratory analyses that changes rapidly. 

Images, mostly acquired through the [CyCIF technology](https://www.cycif.org/), are assumed to be processed first by [mcmicro-nf](https://github.com/labsyspharm/mcmicro-nf), where most of the heavy computation for illumination correction, stitching, registration, nuclei & cell segmentation, and feature quantification are done. The images are then passed to this toolkit for rapid iterations of exploratory analyses.

## Module specification

* ROI slicing

  Slice a small region of interest (ROI), defined using the graphical user interface on [Harvard Medical School OMERO server](https://omero.hms.harvard.edu/), append custom layers (ex. segmentation masks, ROI mask), and then pack into one single ome.tif file with pyramid pre-computed. ROI polygon vertices are exported using a [custom JavaScript script](https://gist.github.com/Yu-AnChen/58754f960ccd540e307ed991bc6901b0). Image pyramid is computed using a [module](https://gist.github.com/jmuhlich/a926f55f7eb115af54c9d4754539bbc1) from [ASHLAR](https://github.com/labsyspharm/ashlar).
  
  * Input:
    * image (ome.tif format)
    * ROI list (csv format)
    * [optional] masks to append (tiff format)
  * Output:
    * smaller image (ome.tif format)

* Tissue integrity

  Pixel intensity correlation coefficient between the first and each subsequent DNA channels. This value serves as a quick, first-pass measure of tissue integrity. Known tissue integrity issues include cell loss and non-linear local deformation that's hard to align by typical image registration methods.
  
  * Input:
    * image (ome.tif format)
  * Output:
    * DNA correlation coefficients (csv format)
    
* Exemplar gallery view

  Visualize individual cells in gallery view format (ex. 10x10=100 cells, in single image) to facilitate visual inspections.
  
  * Input:
    * cell index (note that `histoCAT` resets the index given by segmentation masks)
    * segmentation mask (tiff format)
    * image (ome.tif format)
    * markers (csv format)
    * configuration file (yaml format), ie. what markers to show for which cell types
  * Output:
    * image (png/jpeg format)
