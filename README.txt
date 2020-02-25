Example Python code for quality assessment.

Description:
   Given a folder structure after mcmicro pipeline and some ROI coordinates,
   crop the ROI from each channel and also any mask, and then combine them
   into a single .ome.tif image with the pyramid structure pre-computed.
   Note that this example was designed to be run on the O2 server of Harvard Medical School.
   Note that rotation is currently not implemented because nuclei/cell outlines (1 pixel think)
   lose their integrity in the interpolation phase of the rotation.

What's in this folder:
1. ```README.txt```
   This instruction you are reading right now.
2. ```data```
   A folder with example images.
3. ```code```
   A folder with all the codes needed in this example.
   ```code/slurmjob.sh``` is the job script to be submitted.
   ```code/main.py``` is the main body of the Python code.
   ```code/ashlar_pyramid_hdf5.py``` is a Python code for computing the pyramid structure
                                     required for OMERO server. Slightly modified to use
                                     HDF5 data format (h5py module) instead of the original
                                     format (pytiff module).
   ```code/params.yaml``` is the parameter/configuration file specifying paths and ROI coordinates.
4. ```output```
   A folder for the output files.
5. ```virtualenv```
   A folder for the virtual environment.

Procedure to run this example:
1. On O2, go to the code folder and submit the job script by the following command:
   ```cd code```
   ```sbatch slurmjob.sh```

Procedure to run the code on your images:
1. Make sure your images have been processed through the mcmicro pipeline.
   For more information, check out this website https://labsyspharm.github.io/mcmicro/.
2. Modify the parameter/configuration file using any text editor. For example, use VIM like this:
   ```vim code/params.yaml```
   The format should be self-explanatory. Please direct any question to Hung-Yi at hungyi_wu@g.harvard.edu.
3. Repeat the steps in the "Procedure to run this example" section above.

Please direct any question to Hung-Yi at hungyi_wu@g.harvard.edu.
