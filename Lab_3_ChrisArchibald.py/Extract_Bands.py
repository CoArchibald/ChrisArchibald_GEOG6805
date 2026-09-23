import os
from osgeo import gdal

# Instructor-provided stacked image
input_file = "/Users/chrisarchibald/Desktop/GEOG 6805/Stacked_8bands-1.TIF"

# Folder where the extracted bands will be saved
output_folder = "/Users/chrisarchibald/Desktop/GEOG 6805/Lab_3"

# Open the stacked image
input_dataset = gdal.Open(input_file)

if input_dataset is None:
    raise ValueError("Could not open the input Stacked_8bands-1.TIF file.")

# Get raster information
projection = input_dataset.GetProjection()
geotransform = input_dataset.GetGeoTransform()
driver = gdal.GetDriverByName("GTiff")

# Extract Bands 5, 4, and 3
for band_number in [5, 4, 3]:

    input_band = input_dataset.GetRasterBand(band_number)

    output_file = os.path.join(
        output_folder,
        f"band{band_number}.TIF"
    )

    output_dataset = driver.Create(
        output_file,
        input_dataset.RasterXSize,
        input_dataset.RasterYSize,
        1,
        input_band.DataType
    )

    # Preserve spatial information
    output_dataset.SetProjection(projection)
    output_dataset.SetGeoTransform(geotransform)

    # Copy the raster data
    data = input_band.ReadAsArray()
    output_band = output_dataset.GetRasterBand(1)
    output_band.WriteArray(data)

    # Preserve NoData value
    no_data_value = input_band.GetNoDataValue()

    if no_data_value is not None:
        output_band.SetNoDataValue(no_data_value)

    output_band.FlushCache()
    output_dataset.FlushCache()

    output_dataset = None

    print(f"Created: {output_file}")

input_dataset = None

print("Band extraction complete!")