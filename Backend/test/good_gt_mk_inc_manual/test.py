import geopandas as gpd
import folium
import random

# Load the Shapefile
shapefile_path = "good_gt_mk_inc_manual.shp"
gdf = gpd.read_file(shapefile_path)

# Drop rows where lat/lon are missing
gdf = gdf.dropna(subset=["lat", "lon"])

# Detect the label/class column if it exists
label_col = next((col for col in ["class", "label", "category"] if col in gdf.columns), None)

# Create a Folium map centered at the mean location
center_lat, center_lon = gdf["lat"].mean(), gdf["lon"].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

# Assign colors dynamically for each unique class
color_palette = ["blue", "red", "green", "purple", "orange", "darkblue", "cadetblue", "lightgray"]
class_colors = {}

# Add markers to the map
for _, row in gdf.iterrows():
    label = row[label_col] if label_col else "No Label"

    # Assign a unique color to each class
    if label not in class_colors:
        class_colors[label] = random.choice(color_palette)

    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f"ID: {row.name}<br>Class: {label}",
        icon=folium.Icon(color=class_colors[label], icon="info-sign"),
    ).add_to(m)

# Compute and add a bounding circle around all points
if len(gdf) > 1:
    max_distance = max(
        ((row["lat"] - center_lat) ** 2 + (row["lon"] - center_lon) ** 2) ** 0.5
        for _, row in gdf.iterrows()
    ) * 111000  # Convert degrees to meters

    folium.Circle(
        location=[center_lat, center_lon],
        radius=max_distance,
        color="red",
        fill=True,
        fill_opacity=0.2,
    ).add_to(m)

# Save the map as an HTML file
m.save("map.html")

print("Map has been saved as map.html")
