from flask import Flask, request, send_file , send_from_directory
from flask_cors import CORS
import geopandas as gpd
import folium
import zipfile
import tempfile
import os
import glob

import rasterio
from PIL import Image
import numpy as np


from process_shapefiles import Process
from preProcess import PreProcess_PipeLine
from modelCreationp import modelCreation_PipeLine
from prediction import prediction_PipeLine
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/uploadBoundry', methods=['POST'])
def upload_shapefile():
    file = request.files['shapefile']
    if not file:
        return "No file uploaded", 400

    # Create the save directory
    save_dir = os.path.join(os.getcwd(), 'uploads', 'boundry')
    os.makedirs(save_dir, exist_ok=True)

    # Clear existing files in the directory (optional, to avoid conflicts)
    for f in os.listdir(save_dir):
        os.remove(os.path.join(save_dir, f))

    # Save the uploaded zip
    zip_path = os.path.join(save_dir, file.filename)
    file.save(zip_path)

    # Extract directly into the save_dir (no subfolder)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(save_dir)

    # Find the .shp file
    shp_file = next((f for f in os.listdir(save_dir) if f.endswith('.shp')), None)
    if not shp_file:
        return "Shapefile (.shp) not found in zip", 400

    shp_path = os.path.join(save_dir, shp_file)
    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs(epsg=4326)

    # Compute centroids
    projected = gdf.to_crs(epsg=32644)
    gdf['centroid'] = projected.centroid.to_crs(epsg=4326)

    bounds = gdf.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
    m = folium.Map(location=center, zoom_start=8)

    gdf_clean = gdf.drop(columns=['centroid'])

    folium.GeoJson(
        gdf_clean,
        name="Shapefile",
        style_function=lambda x: {
            'color': 'blue',
            'weight': 2,
            'fillOpacity': 0.1
        }
    ).add_to(m)

    for _, row in gdf.iterrows():
        label = row.get('type', 'No Label')
        point = row['centroid']
        folium.Marker(
            location=[point.y, point.x],
            popup=str(label),
            icon=folium.Icon(color='red')
        ).add_to(m)

    # Save the map in the same directory
    output_path = os.path.join(save_dir, 'map.html')
    m.save(output_path)

    return send_file(output_path, mimetype='text/html')

@app.route('/uploadMarkers', methods=['POST'])
def upload_markers():
    file = request.files['shapefile']
    if not file:
        return "No file uploaded", 400

    # Define permanent directory
    save_dir = os.path.join(os.getcwd(), 'uploads', 'markers')
    os.makedirs(save_dir, exist_ok=True)

    # Optional: Clean existing files before new upload
    for f in os.listdir(save_dir):
        os.remove(os.path.join(save_dir, f))

    # Save and extract ZIP file
    zip_path = os.path.join(save_dir, file.filename)
    file.save(zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(save_dir)

    # Find .shp file
    shp_file = next((f for f in os.listdir(save_dir) if f.endswith('.shp')), None)
    if not shp_file:
        return "Shapefile (.shp) not found in zip", 400

    shp_path = os.path.join(save_dir, shp_file)
    gdf = gpd.read_file(shp_path)

    # Check if geometry is of Point type
    if gdf.geom_type.iloc[0] != 'Point':
        return "Uploaded shapefile must contain point geometries.", 400

    gdf = gdf.to_crs(epsg=4326)
    bounds = gdf.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
    m = folium.Map(location=center, zoom_start=8)

    # Optional: Marker color mapping
    type_colors = {
        'water': 'blue',
        'rice': 'green',
        'wheat': 'orange',
        'maize': 'purple'
    }

    for _, row in gdf.iterrows():
        label = row.get('type', 'No Label')
        color = type_colors.get(str(label).lower(), 'gray')
        geom = row.geometry
        folium.Marker(
            location=[geom.y, geom.x],
            popup=str(label),
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)

    # Save output map
    output_path = os.path.join(save_dir, 'markers_map.html')
    m.save(output_path)

    return send_file(output_path, mimetype='text/html')


@app.route('/processShapefiles', methods=['GET'])
def processShapeFiles():

    directory = '/home/sudharsan/projects/CropMapping/Backend/uploads'
    shp_files = glob.glob(f'{directory}/**/*.shp', recursive=True)


    roi_path = shp_files[0]
    markers_path = shp_files[1]
    
    processShapeFiles = Process(roi_path, markers_path)

    PreProcess_PipeLine(project_name="ujjain")

    modelCreation_PipeLine(
        project_name="ujjain",
        sample_size=400,
        test_size=0.33,
        n_trees=500
    )

    prediction_PipeLine('ujjain')

    return '', 200


@app.route("/Output",methods=['GET'])
def serve_tif():

    project="ujjain"
    InputPath=f"Crop_mapping_{project}/Predicted_Cropmap/output.tif"
    OutputPath=f"Crop_mapping_{project}/Predicted_Cropmap/output.png"

    convert_raster(InputPath,OutputPath)
    
    
    return send_from_directory(f"Crop_mapping_{project}/Predicted_Cropmap/","output.png")



def convert_raster(input_path, output_path):
    with rasterio.open(input_path) as src:
        count = src.count

        if count == 1:
            # Grayscale
            img_array = src.read(1)
            img_array = ((img_array - img_array.min()) / (img_array.max() - img_array.min()) * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode="L")
        elif count >= 3:
            # RGB
            img_array = src.read([1, 2, 3])
            img_array = np.transpose(img_array, (1, 2, 0))  # (bands, height, width) -> (height, width, bands)
            img_array = ((img_array - img_array.min()) / (img_array.max() - img_array.min()) * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
        else:
            raise ValueError("Unsupported band count")

        img.save(output_path)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
