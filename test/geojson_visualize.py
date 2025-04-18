import ee
import geopandas as gpd
import json

try:
    # Initialize Earth Engine
    ee.Initialize(project='ee-sudharsanr836')

    # Load Local Shapefile / GeoJSON
    file_path = "ujjain_dist_shp/output.geojson"
    gdf = gpd.read_file(file_path)

    # Convert to GeoJSON format
    geojson_dict = json.loads(gdf.to_json())

    # Convert to EE FeatureCollection
    roi = ee.FeatureCollection(geojson_dict)

    # Simple Earth Engine operation to test
    try:
        print(roi.first().getInfo()) #print the first feature.
    except ee.ee_exception.EEException as e:
        print(f"Earth Engine Feature Error: {e}")

except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
except json.JSONDecodeError:
    print("Error: Invalid GeoJSON format.")
except ee.ee_exception.EEException as e:
    print(f"Earth Engine Initialization Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

#GeoPandas check.
file_path = "ujjain_dist_shp/output.geojson"
gdf = gpd.read_file(file_path)
print(gdf.crs)