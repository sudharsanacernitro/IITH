import geopandas as gpd
import folium

# Load shapefile
shapefile = gpd.read_file("ujjain_dst.shp")

# Ensure it's in WGS84 for mapping
shapefile = shapefile.to_crs(epsg=4326)

# Calculate centroids (projected CRS first for accuracy)
projected = shapefile.to_crs(epsg=32644)  # Example UTM zone for India (adjust if needed)
shapefile['centroid'] = projected.centroid.to_crs(epsg=4326)  # Convert centroids back to WGS84

# Create map centered on the shapefile
bounds = shapefile.total_bounds
center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
m = folium.Map(location=center, zoom_start=8)

# Drop non-serializable columns before passing to folium
shapefile_clean = shapefile.drop(columns=['centroid'])

# Add shapefile polygons
folium.GeoJson(
    shapefile_clean,
    name="Shapefile",
    style_function=lambda x: {
        'color': 'blue',
        'weight': 2,
        'fillOpacity': 0.1
    }
).add_to(m)

# Add markers at centroids
for _, row in shapefile.iterrows():
    label = row.get('class', 'No Label')  # Change 'class' if needed
    point = row['centroid']
    folium.Marker(
        location=[point.y, point.x],
        popup=str(label),
        icon=folium.Icon(color='red')
    ).add_to(m)

# Save map
m.save("shapefile_map.html")
print("Map saved as shapefile_map.html")
