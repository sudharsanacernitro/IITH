import glob

directory = '/home/sudharsan/projects/CropMapping/Backend/uploads'
shp_files = glob.glob(f'{directory}/**/*.shp', recursive=True)

print(shp_files)
