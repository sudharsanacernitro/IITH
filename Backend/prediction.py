import numpy as np
import rasterio
#from rasterio.transform import from_origin
#from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import joblib
from sklearn.utils.validation import check_is_fitted
import re  # Add import for regular expressions
import os  # Add import for file operations

def crop_map_prediction(input_raster_path, model_path, output_raster_path):
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_raster_path)
    os.makedirs(output_dir, exist_ok=True)
    
    raster = rasterio.open(input_raster_path)
    
    # Get the geotransform and projection
    gt = raster.transform
    proj = raster.crs.to_wkt()
    
    array = raster.read()
    print(array.shape)
    
    # Reshape array
    new_shape = (array.shape[0], array.shape[1] * array.shape[2])
    reshaped_stacked_array = array.reshape(new_shape)
    print(reshaped_stacked_array.shape)
    
    # Swap axes for prediction
    array_for_prediction = np.swapaxes(reshaped_stacked_array, 0, 1)
    print(array_for_prediction.shape)
    print(array_for_prediction)
      
    
    # load model
    loaded_model = joblib.load(model_path)
    
    # Ensure the model is fitted
    check_is_fitted(loaded_model)
    
    # Suppress feature name warning by ensuring compatibility
    if hasattr(loaded_model, "feature_names_in_"):
        loaded_model.feature_names_in_ = None
    
    # pred for full image
    pred = loaded_model.predict(array_for_prediction)
    print(pred.shape)
    print(np.unique(pred))
    
    pred_final=pred.reshape(array.shape[1], array.shape[2])
    print(pred_final.shape)
    
    predimg= pred_final[:,:]
    plt.imshow(predimg)
    
    
    # write predicted array using rasterio
    
    # Get the dimensions of the array
    height, width = pred_final.shape
    
    # Create the output raster dataset using rasterio
    with rasterio.open(
        output_raster_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=array.dtype,
        crs=proj,
        transform=gt,
    ) as dst:
        # Write the array to the output raster
        dst.write(pred_final, 1)
    
 
    
 
project_name = "ujjain"  # Update this variable as needed
project_dir = f"Crop_mapping_{project_name}"

input_raster_path = rf"{project_dir}/raster_stack/S1S2_Ujjain_Rabi_Prediction_stack.tif"

def get_accuracy_from_filename(filename):
    match = re.search(r"_([\d.]+)\.joblib$", filename)
    return match.group(1) if match else "unknown"

def find_model_file(directory, prefix, extension):
    for file in os.listdir(directory):
        if file.startswith(prefix) and file.endswith(extension):
            return file
    raise FileNotFoundError(f"No file found with prefix '{prefix}' and extension '{extension}' in directory '{directory}'.")

# Dynamically determine model path and accuracy
model_dir = rf"{project_dir}/metrics"
model_filename = find_model_file(model_dir, "BRF_crops3inc_multiclass", ".joblib")
accuracy = get_accuracy_from_filename(model_filename)
model_path = rf"{model_dir}/{model_filename}"

# Update output path to include accuracy
output_raster_path = rf"{project_dir}/Predicted_Cropmap/BRF_crops3inc_multiclass_{accuracy}_v01.tif"

crop_map_prediction(input_raster_path=input_raster_path, model_path=model_path, output_raster_path=output_raster_path)