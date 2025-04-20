import ee
import pandas as pd
import io
import os

from local_file_upload import localFeature

# Initialize Earth Engine
ee.Initialize(project='cobalt-mantis-420410')

# --- Inputs ---
roi = localFeature("test/ujjain_dist_shp/ujjain_dst.shp")
prediction_patch_ujjain = localFeature("test/dataPoints/AllMarkersExport.shp")
ujjain_crop_gt_inc = localFeature("test/dataPoints/AllMarkersExport.shp")

start_s1 = '2023-10-01'
end_s1 = '2024-04-30'

start_s2 = '2023-10-15'
end_s2 = '2024-04-30'

# --- Output Folder ---
project_name = "ujjain"
output_folder = f"Crop_mapping_{project_name}"

# Ensure the folder exists
os.makedirs(output_folder, exist_ok=True)

# --- Functions ---
def mosaic_by_date(imcol):
    imlist = imcol.toList(imcol.size())
    unique_dates = imlist.map(lambda im: ee.Image(im).date().format("YYYY-MM-dd")).distinct()

    def mosaic_image(d):
        d = ee.Date(d)
        im = imcol.filterDate(d, d.advance(1, "day")).mosaic()
        return im.set(
            "system:time_start", d.millis(),
            "system:id", d.format("YYYY-MM-dd"),
            "system:index", d.format("YYYYMMdd")
        )

    mosaic_imlist = unique_dates.map(mosaic_image)
    return ee.ImageCollection(mosaic_imlist)

def add_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

def temporal_collection(collection, start, count, interval, units):
    sequence = ee.List.sequence(0, ee.Number(count).subtract(1))
    original_start_date = ee.Date(start)

    def temporal_image(i):
        start_date = original_start_date.advance(ee.Number(interval).multiply(i), units)
        end_date = original_start_date.advance(ee.Number(interval).multiply(ee.Number(i).add(1)), units)
        return collection.filterDate(start_date, end_date).max().set(
            'system:time_start', start_date.millis(),
            'system:time_end', end_date.millis(),
            "system:id", start_date.format("YYYY-MM-dd"),
            "system:index", start_date.format("YYYY-MM-dd")
        )

    return ee.ImageCollection(sequence.map(temporal_image))

def extract_time_series(collection, points, band_name):
    # Debugging: Print available feature properties
    sample_feature = points.first()
    print("Available feature properties (columns):", sample_feature.propertyNames().getInfo())

    # Debugging: Print unique values in the 'type' column
    if 'type' in sample_feature.propertyNames().getInfo():
        unique_types = points.aggregate_array('type').distinct().getInfo()
        print("Unique values in 'type' column:", unique_types)
    else:
        print("Column 'type' is missing in the features.")

    def extract_feature_values(image):
        def format_feature(feature):
            coords = ee.List(feature.geometry().centroid().coordinates())
            lat = coords.get(1)
            lon = coords.get(0)
            return feature.set({
                band_name: ee.List([feature.get(band_name), -9999]).reduce(ee.Reducer.firstNonNull()),
                'imageID': image.id(),
                'date': image.get('system:index'),
                'lat': lat,
                'lon': lon,
                'id': ee.Algorithms.If(feature.get('id'), feature.get('id'), ""),  # fallback if missing
                'crpname_eg': ee.Algorithms.If(feature.get('type'), feature.get('type'), 'unknown'),
                'geometry': ""
            }).copyProperties(feature)  # <- this keeps 'type' and other original props!



        return image.select(band_name).reduceRegions(
            collection=points,
            reducer=ee.Reducer.mean().setOutputs([band_name]),
            scale=10,
        ).map(format_feature)

    return collection.map(extract_feature_values).flatten()


def export_table_to_pandas(feature_collection, selectors):
    """Exports an Earth Engine FeatureCollection to a Pandas DataFrame."""
    table = feature_collection.select(selectors)
    data = table.getInfo()['features']
    df = pd.DataFrame([f['properties'] for f in data])
    return df

print("Starting Sentinel-1 processing...")
# --- Sentinel-1 Processing ---
s1 = ee.ImageCollection("COPERNICUS/S1_GRD").filterDate(start_s1, end_s1).filterBounds(roi).filter(ee.Filter.eq('instrumentMode', 'IW')).filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')).map(lambda image: image.clip(roi)).select('VV', 'VH')
s1_mosaic = mosaic_by_date(s1)
s1_vv = s1_mosaic.select('VV')
s1_vh = s1_mosaic.select('VH')

print("Extracting Sentinel-1 VV time series...")
# --- Sentinel-1 Time Series Extraction and Export ---
vv_triplets = extract_time_series(s1_vv, ujjain_crop_gt_inc, 'VV')
print("Extracting Sentinel-1 VH time series...")
vh_triplets = extract_time_series(s1_vh, ujjain_crop_gt_inc, 'VH')

print("Exporting Sentinel-1 VV data to CSV...")
vv_df = export_table_to_pandas(vv_triplets, ['id', 'date', 'VV', 'crpname_eg', 'lat', 'lon', 'geometry'])
vv_df.to_csv(f'{output_folder}/VV_timeseries_{project_name}_crops3inc.csv', index=False)

print("Exporting Sentinel-1 VH data to CSV...")
vh_df = export_table_to_pandas(vh_triplets, ['id', 'date', 'VH', 'crpname_eg', 'lat', 'lon', 'geometry'])
vh_df.to_csv(f'{output_folder}/VH_timeseries_{project_name}_crops3inc.csv', index=False)

print("Starting Sentinel-2 processing...")
# --- Sentinel-2 Processing ---
s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate(start_s2, end_s2).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50)).filterBounds(roi).map(lambda image: image.clip(roi))
s2_mosaic = mosaic_by_date(s2)
s2_ndvi = s2_mosaic.map(add_ndvi).select('NDVI')
ndvi_16days = temporal_collection(s2_ndvi, start_s2, 13, 16, 'day')

print("Extracting Sentinel-2 NDVI time series...")
# --- Sentinel-2 Time Series Extraction and Export ---
ndvi_triplets = extract_time_series(ndvi_16days, ujjain_crop_gt_inc, 'NDVI')
print("Exporting Sentinel-2 NDVI data to CSV...")
ndvi_df = export_table_to_pandas(ndvi_triplets, ['id', 'date', 'NDVI', 'crpname_eg', 'lat', 'lon', 'geometry'])
ndvi_df.to_csv(f'{output_folder}/NDVI_timeseries_{project_name}_crops3inc.csv', index=False)

print("Time series data exported to CSV files.")