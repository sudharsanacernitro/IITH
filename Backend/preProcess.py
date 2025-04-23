import os
import glob
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

def process_time_series(input_file_path, output_file_path, prefix, data_type):
    print(f"Processing {input_file_path}...")
    df_tall = pd.read_csv(input_file_path)
    
    if data_type == 'crop':
        if 'crpname_eg' not in df_tall.columns:
            raise KeyError("The 'crpname_eg' column is missing from the input DataFrame.")
        index_columns = ['id', 'crpname_eg', 'lat', 'lon']

    df_tall['id'] = range(1, len(df_tall) + 1)
    all_dates = df_tall['date'].unique().tolist()
    pivot_df = df_tall.pivot(index=index_columns, columns='date', values=prefix)
    pivot_df.reset_index(inplace=True)
    pivot_df = pivot_df.reindex(columns=index_columns + all_dates)
    df_moved_up = pivot_df.apply(lambda x: x.dropna().reset_index(drop=True))
    for col in pivot_df.columns[2:]:
        pivot_df[col] = df_moved_up[col]
    pivot_df = pivot_df.dropna()
    pivot_df.to_csv(output_file_path, index=False)
    return pivot_df

def add_prefix_to_features(directory, output_path, drop_cols=None):
    files = glob.glob(f"{directory}/*_wide.csv")
    print(f"Files found for merging: {files}")
    dataframes = {}

    for file_path in files:
        if 'VV' in file_path:
            dtype = 'VV'
        elif 'VH' in file_path:
            dtype = 'VH'
        elif 'NDVI' in file_path:
            dtype = 'NDVI'
        else:
            continue
        print(f"Processing file: {file_path} as {dtype}")
        df = pd.read_csv(file_path)
        df.columns = [f'{dtype}_{col}' if col[0].isdigit() else col for col in df.columns]
        dataframes[dtype] = df

    if not all(key in dataframes for key in ['VV', 'VH', 'NDVI']):
        missing = [key for key in ['VV', 'VH', 'NDVI'] if key not in dataframes]
        raise ValueError(f"All three datasets (VV, VH, NDVI) are required. Missing: {missing}")

    index_crop = ['id', 'crpname_eg', 'lat', 'lon']
    gt_crop = pd.merge(
        pd.merge(dataframes['VV'], dataframes['VH'], on=index_crop, how='inner'),
        dataframes['NDVI'], on=index_crop, how='inner'
    )
    gt_crop = gt_crop[~(gt_crop.isin([-9999.000000]).any(axis=1))]

    if drop_cols:
        gt_crop.drop(drop_cols, axis=1, inplace=True)

    gt_crop.to_csv(output_path, index=False)
    return gt_crop

def assign_class_values(input_file, output_file_path):
    gt_crop = input_file
    unique_crops = input_file['crpname_eg'].unique()
    crop_map = {crop: idx + 1 for idx, crop in enumerate(unique_crops)}
    gt_crop['Class'] = gt_crop['crpname_eg'].map(crop_map).fillna(0).astype(int)
    cols_to_drop = ['crpname_eg', 'lat', 'lon']
    gt_crop = gt_crop.drop(cols_to_drop, axis=1)
    gt_crops3inc = gt_crop.drop('id', axis=1)
    gt_crops3inc.reset_index(drop=True)
    gt_crops3inc.to_csv(output_file_path, index=False)
    return gt_crops3inc

def plot_timeseries(df, prefix, file_name):
    crop_names = {1: "Wheat", 2: "Gram", 3: "Mustard"}
    crops_to_plot = [1, 2, 3]
    crop_dfs = {}

    for crop in crops_to_plot:
        df_crop = df[df['Class'] == crop]
        df_crop = df_crop.filter(like=prefix)
        df_cleaned = df_crop[~(df_crop.isin([-9999.000000]).any(axis=1))]
        mean_values = df_cleaned.mean(axis=0)
        std_values = df_cleaned.std(axis=0)
        crop_dfs[crop] = (mean_values, std_values)

    plt.figure(figsize=(12, 10), dpi=80)
    colors = ['Red', 'Green', 'Blue']

    for idx, crop in enumerate(crops_to_plot):
        mean_values, std_values = crop_dfs[crop]
        plt.plot(mean_values, marker=None, color=colors[idx], label=f'{crop_names[crop]} Mean')
        plt.fill_between(
            range(len(mean_values)),
            mean_values - std_values,
            mean_values + std_values,
            color=colors[idx], alpha=0.2, label=f'{crop_names[crop]} Standard Deviation'
        )

    plt.legend(loc='upper right')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel(prefix.strip('_'))
    plt.xlabel('Date')
    plt.title(f"{prefix.strip('_')} Timeseries for Crops Wheat, Gram, Mustard", fontweight='bold')
    plt.grid()
    plt.savefig(file_name)
    plt.close()
    print(f"Plot saved as {file_name}")

def PreProcess_PipeLine(project_name="ujjain"):
    input_dir = f"Crop_mapping_{project_name}"
    output_dir = os.path.join(input_dir, "timeseries")
    os.makedirs(output_dir, exist_ok=True)

    input_files = [
        os.path.join(input_dir, f"VV_timeseries_{project_name}.csv"),
        os.path.join(input_dir, f"VH_timeseries_{project_name}.csv"),
        os.path.join(input_dir, f"NDVI_timeseries_{project_name}.csv")
    ]

    for input_file_path in input_files:
        dir_name, file_name = os.path.split(input_file_path)
        base, ext = os.path.splitext(file_name)
        output_file_path = os.path.join(output_dir, f"{base}_wide{ext}")
        prefix = base.split('_')[0]
        print(f"Running conversion for {input_file_path} with {prefix}{output_file_path}...")
        process_time_series(input_file_path, output_file_path, prefix, data_type='crop')

    output_file = os.path.join(output_dir, "timeseries_crops3inc.csv")
    drop_cols = ['NDVI_2023-10-31']
    gt_crop_3bands = add_prefix_to_features(directory=output_dir, output_path=output_file, drop_cols=drop_cols)

    output_file_path = os.path.join(output_dir, "crops3inc_multiclass_S1S2_onlytimeseries_v01.csv")
    final_csv = assign_class_values(input_file=gt_crop_3bands, output_file_path=output_file_path)

    prefixes = ['VV_', 'VH_', 'NDVI_']
    plot_dir = os.path.join(input_dir, "timeseries_trend_figures")
    os.makedirs(plot_dir, exist_ok=True)

    for prefix in prefixes:
        plot_timeseries(final_csv, prefix, os.path.join(plot_dir, f"{prefix}Timeseries.png"))

# Run the entire flow
if __name__ == "__main__":
    PreProcess_PipeLine("ujjain")
