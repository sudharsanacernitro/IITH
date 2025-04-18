import geopandas as gpd

# Load the Shapefile
shapefile_path = "good_gt_mk_inc_manual.shp"
gdf = gpd.read_file(shapefile_path)

# Check first few rows
print(gdf[['lat', 'lon', 'latitude', 'longitude']].head())
print("Geometry Type:\n", gdf.geom_type.value_counts())
