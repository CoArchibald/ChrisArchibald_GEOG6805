import os
from glob import glob
from osgeo import gdal

# Folder containing the Landsat 8 bands
your_directory = "/Users/chrisarchibald/Desktop/GEOG 6805/Lab_3/LC08_L1TP_038032_20230621_20230630_02_T1"

# Find bands B1-B7 and B9
unsorted_list = glob(os.path.join(your_directory, "*_B[1-7,9].TIF"))

# Sort the band files
sorted_list = sorted(unsorted_list)

# Print the files that will be stacked
print("Bands found:")
for file in sorted_list:
    print(file)

# Make sure we found all 8 required bands
if len(sorted_list) != 8:
    raise ValueError(f"Expected 8 bands, but found {len(sorted_list)}")

# Open the first band to get the raster information
first_dataset = gdal.Open(sorted_list[0])

x_size = first_dataset.RasterXSize
y_size = first_dataset.RasterYSize
projection = first_dataset.GetProjection()
geotransform = first_dataset.GetGeoTransform()

first_band = first_dataset.GetRasterBand(1)
data_type = first_band.DataType
no_data_value = first_band.GetNoDataValue()

# Create the output stacked TIFF
output_file = os.path.join(your_directory, "Stacked_8bands.TIF")

driver = gdal.GetDriverByName("GTiff")

output_dataset = driver.Create(
    output_file,
    x_size,
    y_size,
    len(sorted_list),
    data_type
)

# Keep the original projection and spatial information
output_dataset.SetProjection(projection)
output_dataset.SetGeoTransform(geotransform)

# Copy each band into the stacked TIFF
for i, file in enumerate(sorted_list, start=1):

    input_dataset = gdal.Open(file)
    input_band = input_dataset.GetRasterBand(1)

    data = input_band.ReadAsArray()

    output_band = output_dataset.GetRasterBand(i)
    output_band.WriteArray(data)

    # Keep the original NoData value
    if no_data_value is not None:
        output_band.SetNoDataValue(no_data_value)

    output_band.FlushCache()

    input_dataset = None

# Finish writing the output file
output_dataset.FlushCache()
output_dataset = None
first_dataset = None

print("Stacking complete!")
print("Output file:")
print(output_file)