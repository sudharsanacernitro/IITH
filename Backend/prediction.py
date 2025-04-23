import os
import re
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import joblib
from sklearn.utils.validation import check_is_fitted

def ensure_output_directory(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def load_raster(raster_path):
    raster = rasterio.open(raster_path)
    array = raster.read()
    return raster, array

def reshape_raster_for_prediction(array):
    reshaped_array = array.reshape((array.shape[0], array.shape[1] * array.shape[2]))
    array_for_prediction = np.swapaxes(reshaped_array, 0, 1)
    return array_for_prediction

def load_trained_model(model_path):
    model = joblib.load(model_path)
    check_is_fitted(model)
    if hasattr(model, "feature_names_in_"):
        model.feature_names_in_ = None  # To suppress feature name warning
    return model

def predict_crop_map(model, data, original_shape):
    pred = model.predict(data)
    pred_reshaped = pred.reshape(original_shape[1], original_shape[2])
    return pred_reshaped

def save_prediction_raster(output_path, data, reference_raster):
    ensure_output_directory(output_path)
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=reference_raster.crs.to_wkt(),
        transform=reference_raster.transform,
    ) as dst:
        dst.write(data, 1)

def display_prediction(prediction_array):
    plt.imshow(prediction_array, cmap='viridis')
    plt.title("Predicted Crop Map")
    plt.colorbar()
    plt.show()

def get_accuracy_from_filename(filename):
    match = re.search(r"_([\d.]+)\.joblib$", filename)
    return match.group(1) if match else "unknown"

def find_model_file(directory, prefix, extension):
    for file in os.listdir(directory):
        if file.startswith(prefix) and file.endswith(extension):
            return file
    raise FileNotFoundError(f"No file found with prefix '{prefix}' and extension '{extension}' in directory '{directory}'.")

def crop_map_prediction_pipeline(input_raster_path, model_path, output_raster_path):
    raster, array = load_raster(input_raster_path)
    print("Original raster shape:", array.shape)

    prediction_input = reshape_raster_for_prediction(array)
    print("Prepared input shape:", prediction_input.shape)

    model = load_trained_model(model_path)
    prediction = predict_crop_map(model, prediction_input, array.shape)

    print("Prediction shape:", prediction.shape)
    print("Unique classes predicted:", np.unique(prediction))

    display_prediction(prediction)
    save_prediction_raster(output_raster_path, prediction, raster)
    print(f"Saved prediction raster at: {output_raster_path}")

def prediction_PipeLine(project_name="ujjain"):
    project_dir = f"Crop_mapping_{project_name}"

    input_raster_path = os.path.join(project_dir, "raster_stack", f"S1S2_{project_name.capitalize()}_Rabi_Prediction_stack.tif")

    model_dir = os.path.join(project_dir, "metrics")
    model_filename = find_model_file(model_dir, "BRF_crops3inc_multiclass", ".joblib")
    accuracy = get_accuracy_from_filename(model_filename)
    model_path = os.path.join(model_dir, model_filename)

    output_raster_path = os.path.join(
        project_dir, "Predicted_Cropmap", f"output.tif"
    )

    crop_map_prediction_pipeline(input_raster_path, model_path, output_raster_path)

if __name__ == "__main__":
    prediction_PipeLine("ujjain")
