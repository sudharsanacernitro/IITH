from flask import Flask, request, send_file
from flask_cors import CORS
import geopandas as gpd
import folium
import zipfile
import tempfile
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/uploadBoundry', methods=['POST'])
def upload_shapefile():
    file = request.files['shapefile']
    if not file:
        return "No file uploaded", 400

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'shapefile.zip')
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        shp_file = next((f for f in os.listdir(tmpdir) if f.endswith('.shp')), None)
        if not shp_file:
            return "Shapefile (.shp) not found in zip", 400

        gdf = gpd.read_file(os.path.join(tmpdir, shp_file))
        gdf = gdf.to_crs(epsg=4326)

        projected = gdf.to_crs(epsg=32644)  # UTM zone for centroid
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
            label = row.get('type', 'No Label')  # ← adjusted to type
            point = row['centroid']
            folium.Marker(
                location=[point.y, point.x],
                popup=str(label),
                icon=folium.Icon(color='red')
            ).add_to(m)

        output_path = os.path.join(tmpdir, 'map.html')
        m.save(output_path)

        return send_file(output_path, mimetype='text/html')


@app.route('/uploadMarkers', methods=['POST'])
def upload_markers():
    file = request.files['shapefile']
    if not file:
        return "No file uploaded", 400

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'markers.zip')
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        shp_file = next((f for f in os.listdir(tmpdir) if f.endswith('.shp')), None)
        if not shp_file:
            return "Shapefile (.shp) not found in zip", 400

        gdf = gpd.read_file(os.path.join(tmpdir, shp_file))

        if gdf.geom_type.iloc[0] != 'Point':
            return "Uploaded shapefile must contain point geometries.", 400

        gdf = gdf.to_crs(epsg=4326)
        bounds = gdf.total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        m = folium.Map(location=center, zoom_start=8)

        # Optional: Define colors for marker types
        type_colors = {
            'water': 'blue',
            'rice': 'green',
            'wheat': 'orange',
            'maize': 'purple'
        }

        for _, row in gdf.iterrows():
            label = row.get('type', 'No Label')
            color = type_colors.get(label.lower(), 'gray')  # fallback color
            geom = row.geometry
            folium.Marker(
                location=[geom.y, geom.x],
                popup=str(label),
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)

        output_path = os.path.join(tmpdir, 'markers_map.html')
        m.save(output_path)

        return send_file(output_path, mimetype='text/html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
