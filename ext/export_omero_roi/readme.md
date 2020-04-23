## Purpose
Export ROIs generated in the PathViewer UI for downstream analysis.

## Execution 
1. In google chrome, go the hms omero and make sure you are logged in
1. In any of your chrome tab/window, hit F12 to launch the developer tools
1. In the console tab of the DevTools paste in the above script
1. Replace the `imgId` with your image ID
1. Hit enter to run, it will ask you to save a csv file, your rois will be in there.

## Output
A csv file `image_name-image_id-rois.csv`, each row is one ROI and the column headers are - 
|Name|type|all_points|X|Y|RadiusX|RadiusY|Width|Height|all_transforms|
|---|---|---|---|---|---|---|---|---|---|

- Name: name of the roi
- type: type of the roi, refer to reference 1
- all_points: coordinates for all corners `"x1,y1 x2,y2 x3,y3 ..."`
- X, Y, RadiusX, RadiusY, Width, Height: refer to reference 1
- all_transforms: refer to reference 2, `"A00,A01,A02,A10,A11,A12,0,0,1"`
- If the property does not exist for the shape, `-1` is used as placeholder
- For ellipse, the four points are the vertices and co-vertices

## Reference
1. [OMERO ROI model](https://docs.openmicroscopy.org/ome-model/5.6.3/developers/roi.html)
2. [Affine Transformations of ROI Shapes](http://blog.openmicroscopy.org/data-model/future-plans/2016/06/20/shape-transforms/)