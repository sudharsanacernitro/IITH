import ee
import geopandas as gpd
import json

ee.Initialize(project='ee-sudharsanr836')



def localFeature(local_shapefile_path):

    gdf = gpd.read_file(local_shapefile_path)

    # Convert to WGS84 (lat/lon), required for Earth Engine
    gdf = gdf.to_crs(epsg=4326)

    # Convert GeoDataFrame to a list of ee.Feature objects
    features = []
    for index, row in gdf.iterrows():
        geojson_geometry = json.loads(json.dumps(row.geometry.__geo_interface__))
        ee_geometry = ee.Geometry(geojson_geometry)
        
        # Remove any non-serializable values from properties
        props = {k: v for k, v in row.to_dict().items() if isinstance(v, (str, int, float, bool, type(None)))}
        
        feature = ee.Feature(ee_geometry, props)
        features.append(feature)

    # Create an ee.FeatureCollection from the list
    local_fc = ee.FeatureCollection(features)

    return local_fc


