import ee
import pandas as pd
import os
from local_file_upload import localFeature


# Initialize Earth Engine
ee.Initialize(project='ee-sudharsanr836')


# --- Utility Functions ---
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

    return ee.ImageCollection(unique_dates.map(mosaic_image))


def add_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)


def temporal_collection(collection, start, count, interval, units):
    sequence = ee.List.sequence(0, ee.Number(count).subtract(1))
    original_start_date = ee.Date(start)

    def temporal_image(i):
        start_date = original_start_date.advance(ee.Number(interval).multiply(i), units)
        end_date = start_date.advance(interval, units)
        return collection.filterDate(start_date, end_date).max().set(
            'system:time_start', start_date.millis(),
            'system:time_end', end_date.millis(),
            'system:id', start_date.format("YYYY-MM-dd"),
            'system:index', start_date.format("YYYY-MM-dd")
        )

    return ee.ImageCollection(sequence.map(temporal_image))


def extract_time_series(collection, points, band_name):
    def extract_feature_values(image):
        def format_feature(feature):
            coords = ee.List(feature.geometry().centroid().coordinates())
            return feature.set({
                band_name: ee.List([feature.get(band_name), -9999]).reduce(ee.Reducer.firstNonNull()),
                'imageID': image.id(),
                'date': image.get('system:index'),
                'lat': coords.get(1),
                'lon': coords.get(0),
                'id': ee.Algorithms.If(feature.get('id'), feature.get('id'), ""),
                'crpname_eg': ee.Algorithms.If(feature.get('type'), feature.get('type'), 'unknown'),
                'geometry': ""
            }).copyProperties(feature)

        return image.select(band_name).reduceRegions(
            collection=points,
            reducer=ee.Reducer.mean().setOutputs([band_name]),
            scale=10,
        ).map(format_feature)

    return collection.map(extract_feature_values).flatten()


def export_table_to_pandas(feature_collection, selectors):
    table = feature_collection.select(selectors)
    data = table.getInfo()['features']
    return pd.DataFrame([f['properties'] for f in data])


# --- Core Processing Function ---
def process_crop_time_series(roi_path, markers_path, start_s1, end_s1, start_s2, end_s2, output_folder, project_name):
    roi = localFeature(roi_path)
    crop_points = localFeature(markers_path)

    os.makedirs(output_folder, exist_ok=True)

    print("Processing Sentinel-1...")
    s1 = ee.ImageCollection("COPERNICUS/S1_GRD") \
        .filterDate(start_s1, end_s1) \
        .filterBounds(roi) \
        .filter(ee.Filter.eq('instrumentMode', 'IW')) \
        .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')) \
        .map(lambda image: image.clip(roi)) \
        .select('VV', 'VH')

    s1_mosaic = mosaic_by_date(s1)
    vv_triplets = extract_time_series(s1_mosaic.select('VV'), crop_points, 'VV')
    vh_triplets = extract_time_series(s1_mosaic.select('VH'), crop_points, 'VH')

    vv_df = export_table_to_pandas(vv_triplets, ['id', 'date', 'VV', 'crpname_eg', 'lat', 'lon', 'geometry'])
    vv_df.to_csv(f'{output_folder}/VV_timeseries_{project_name}.csv', index=False)

    vh_df = export_table_to_pandas(vh_triplets, ['id', 'date', 'VH', 'crpname_eg', 'lat', 'lon', 'geometry'])
    vh_df.to_csv(f'{output_folder}/VH_timeseries_{project_name}.csv', index=False)

    print("Processing Sentinel-2 NDVI...")
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterDate(start_s2, end_s2) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50)) \
        .filterBounds(roi) \
        .map(lambda image: image.clip(roi))

    s2_ndvi = mosaic_by_date(s2).map(add_ndvi).select('NDVI')
    ndvi_16days = temporal_collection(s2_ndvi, start_s2, 13, 16, 'day')

    ndvi_triplets = extract_time_series(ndvi_16days, crop_points, 'NDVI')
    ndvi_df = export_table_to_pandas(ndvi_triplets, ['id', 'date', 'NDVI', 'crpname_eg', 'lat', 'lon', 'geometry'])
    ndvi_df.to_csv(f'{output_folder}/NDVI_timeseries_{project_name}.csv', index=False)

    print("All data exported successfully!")


# --- Main Entry ---
def Process(boundry_path,markers_path):
    
    project_name = "ujjain"
    output_folder = f"Crop_mapping_{project_name}"

    start_s1 = '2023-10-01'
    end_s1 = '2024-04-30'

    start_s2 = '2023-10-15'
    end_s2 = '2024-04-30'

    process_crop_time_series(
        roi_path=boundry_path,
        markers_path=markers_path,
        start_s1=start_s1,
        end_s1=end_s1,
        start_s2=start_s2,
        end_s2=end_s2,
        output_folder=output_folder,
        project_name=project_name
    )

    

if __name__ == "__main__":
    Process()
