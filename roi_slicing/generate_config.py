import yaml

if __name__ == '__main__':
    conf_dict = {
            'image_name1': {
                'image_filepath': '/path/to/image.ome.tif',
                'roi_filepath': '/path/to/roi_list.csv',
                'markers_filepath': '/path/to/markers.csv',
                'mask_nuclei': {
                    'filepath': '/path/to/nucleiRingOutlines.tif',
                    },
                'mask_cell': {
                    'filepath': '/path/to/cellRingOutlines.tif',
                    },
                },
            }

    with open('config.yaml', 'w') as outfile:
        yaml.dump(conf_dict, outfile)
