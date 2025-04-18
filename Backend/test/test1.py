import ee
import pandas as pd




#ee.Authenticate()
# Authenticate and initialize Earth Engine
ee.Initialize(project='ee-sudharsanr836')

# Define region of interest (ROI) as a Polygon
roi = ee.Geometry.Polygon([
    [ [75.6945, 23.1766], [75.9642, 23.1766], [75.9642, 23.5342], [75.6945, 23.5342], [75.6945, 23.1766] ]
])

# Convert to FeatureCollection (for compatibility)
roi_fc = ee.FeatureCollection([ee.Feature(roi)])

# Sentinel-1 Processing
start_date = '2023-10-01'
end_date = '2024-04-30'


s1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
      .filterDate(start_date, end_date)
      .filterBounds(roi)
      .filter(ee.Filter.eq('instrumentMode', 'IW'))
      .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
      .map(lambda img: img.clip(roi))
      .select(['VV', 'VH']))

print("Sentinel-1 Data:", s1.size().getInfo())

# Function to extract time series data
def extract_timeseries(collection, band):
    def reduce_region(image):
        reduced = image.select(band).reduceRegions(
            collection=roi_fc,
            reducer=ee.Reducer.mean(),
            scale=10
        ).map(lambda f: f.set({'date': image.date().format('YYYY-MM-dd')}))
        return reduced

    triplets = collection.map(reduce_region).flatten()
    return triplets

# Extract VV and VH time series
vv_timeseries = extract_timeseries(s1, 'VV')
vh_timeseries = extract_timeseries(s1, 'VH')

# Convert to Pandas DataFrame and Export
def ee_to_df(feature_collection):
    features = feature_collection.getInfo()['features']
    data = [{**f['properties'], 'geometry': f['geometry']} for f in features]
    return pd.DataFrame(data)

df_vv = ee_to_df(vv_timeseries)
df_vh = ee_to_df(vh_timeseries)

df_vv.to_csv("VV_timeseries.csv", index=False)
df_vh.to_csv("VH_timeseries.csv", index=False)

print("Exported VV and VH timeseries to CSV files.")
