import os
import sys
import csv

import numpy as np
import pandas as pd
import tqdm

from sklearn import linear_model

if __name__ == '__main__':
    # paths
    ws_folderpath = '/home/hywu0110/workspace_scale'
    feature_folderpath = os.path.join(ws_folderpath, 'data')
    bkvec_filepath = os.path.join(ws_folderpath, sys.argv[1])
    output_filepath = os.path.join(ws_folderpath, 'feature_cal.csv')

    # cleanup
    bkvec_df = pd.read_csv(bkvec_filepath)
    bkvec_df.rename({'SOX2': 'SOX2_1', 'SOX2.1': 'SOX2_2'}, axis='columns', inplace=True)

    # linear regression
    marker_col = bkvec_df.columns[2:]
#    ref_index = bkvec_df.index[(bkvec_df['slide_id']=='Z170_1') &\
#            (bkvec_df['roi_row_id']==0)][0]
    ref_index = 1
    ref_vec = bkvec_df.loc[ref_index, marker_col].values.flatten()

    def regression(row):
        vec = row[marker_col].values.astype(float)
        mask = np.isfinite(vec)
        if mask.sum() < 2:
            return np.nan, np.nan
        else:
            x = vec[mask].reshape((-1,1))
            y = ref_vec[mask]
            model = linear_model.LinearRegression()
            model.fit(x, y)
            return model.coef_[0], model.intercept_

    coef_df = bkvec_df.apply(regression, axis='columns', result_type='expand')
    coef_df.columns = ['slope', 'intercept']
    coef_df = pd.concat([coef_df, bkvec_df[['slide_id', 'roi_row_id']]],
            axis='columns')

    # transform
    feature_list = []
    feature_col = ['log10({})'.format(col) for col in marker_col]

    header = feature_col + ['CellID', 'slide_id', 'roi_row_id']
    outfile = open(output_filepath, 'w', newline='')
    outwriter = csv.writer(outfile, delimiter=',')
    outwriter.writerow(header)

    for index in tqdm.tqdm(coef_df.index):
        row = coef_df.loc[index]
        # load data
        name = '{}_{}.csv'.format(row['slide_id'], row['roi_row_id'])
        feature_filepath = os.path.join(feature_folderpath, name)
        feature_df = pd.read_csv(feature_filepath)

        # preprocess
        end_index = list(feature_df.columns).index('X_position')
        X = np.log10(feature_df[feature_df.columns[1:end_index]].values)
        Y = row['slope'] * X + row['intercept']
        df = pd.DataFrame(Y, columns=range(Y.shape[1]), index=range(Y.shape[0]))
        df.insert(0, 'CellID', feature_df['CellID'].values)
        df.insert(0, 'slide_id', row['slide_id'])
        df.insert(0, 'roi_row_id', row['roi_row_id'])

        outwriter.writerows(df.values.tolist())
        outfile.flush()

    outfile.close()
