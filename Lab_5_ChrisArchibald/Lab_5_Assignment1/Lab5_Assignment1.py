
import os
import numpy as np
from osgeo import gdal

gdal.UseExceptions()

# Define input and output folders
input_folder = "Input"
output_folder = "Output"

# Create the output folder if it does not exist
os.makedirs(output_folder, exist_ok=True)

# Find Landsat scene folders, ignoring hidden files
scenes = [
    scene for scene in os.listdir(input_folder)
    if os.path.isdir(os.path.join(input_folder, scene))
    and not scene.startswith(".")
]

scenes.sort()

print("Landsat scenes found:")
for scene in scenes:
    print(scene)


def read_band(file_path):
    """Read a Landsat band and return its pixels, dataset, and no-data value."""
    dataset = gdal.Open(file_path)

    if dataset is None:
        raise FileNotFoundError(f"Could not open: {file_path}")

    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray().astype(np.float32)
    nodata = band.GetNoDataValue()

    return array, dataset, nodata


def calculate_indices(
    green, red, nir, swir1,
    green_nodata=None, red_nodata=None,
    nir_nodata=None, swir1_nodata=None, L=0.5
):
    """Calculate and return SAVI and NDSI for one Landsat scene."""

    # Calculate SAVI using NIR (Band 4) and Red (Band 3)
    savi_denominator = nir + red + L
    savi = np.full(nir.shape, -9999.0, dtype=np.float32)

    savi_valid = np.isfinite(nir) & np.isfinite(red)

    if nir_nodata is not None:
        savi_valid &= nir != nir_nodata

    if red_nodata is not None:
        savi_valid &= red != red_nodata

    savi_valid &= savi_denominator != 0

    np.divide(
        (1 + L) * (nir - red),
        savi_denominator,
        out=savi,
        where=savi_valid
    )

    # Calculate NDSI using Green (Band 2) and SWIR1 (Band 5)
    ndsi_denominator = green + swir1
    ndsi = np.full(green.shape, -9999.0, dtype=np.float32)

    ndsi_valid = np.isfinite(green) & np.isfinite(swir1)

    if green_nodata is not None:
        ndsi_valid &= green != green_nodata

    if swir1_nodata is not None:
        ndsi_valid &= swir1 != swir1_nodata

    ndsi_valid &= ndsi_denominator != 0

    np.divide(
        green - swir1,
        ndsi_denominator,
        out=ndsi,
        where=ndsi_valid
    )

    return savi, ndsi


def save_index(output_path, array, reference_dataset):
    """Save an index array as a georeferenced GeoTIFF."""

    driver = gdal.GetDriverByName("GTiff")

    output_dataset = driver.Create(
        output_path,
        reference_dataset.RasterXSize,
        reference_dataset.RasterYSize,
        1,
        gdal.GDT_Float32
    )

    if output_dataset is None:
        raise RuntimeError(f"Could not create output: {output_path}")

    output_dataset.SetGeoTransform(
        reference_dataset.GetGeoTransform()
    )
    output_dataset.SetProjection(
        reference_dataset.GetProjection()
    )

    output_band = output_dataset.GetRasterBand(1)
    output_band.SetNoDataValue(-9999.0)
    output_band.WriteArray(array)
    output_band.FlushCache()

    output_band = None
    output_dataset = None


# Loop through each Landsat scene
for scene in scenes:
    print(f"\nProcessing scene: {scene}")

    scene_folder = os.path.join(input_folder, scene)

    # Build paths to the required Landsat bands
    band_paths = {
        "B2": os.path.join(scene_folder, f"{scene}_B2.TIF"),
        "B3": os.path.join(scene_folder, f"{scene}_B3.TIF"),
        "B4": os.path.join(scene_folder, f"{scene}_B4.TIF"),
        "B5": os.path.join(scene_folder, f"{scene}_B5.TIF"),
    }

    # Read the required bands
    green, green_ds, green_nodata = read_band(band_paths["B2"])
    red, red_ds, red_nodata = read_band(band_paths["B3"])
    nir, nir_ds, nir_nodata = read_band(band_paths["B4"])
    swir1, swir1_ds, swir1_nodata = read_band(band_paths["B5"])

    # Calculate SAVI and NDSI using one function
    savi, ndsi = calculate_indices(
        green, red, nir, swir1,
        green_nodata, red_nodata,
        nir_nodata, swir1_nodata
    )

    # Save results using the scene identifier in each filename
    savi_path = os.path.join(output_folder, f"{scene}_SAVI.tif")
    ndsi_path = os.path.join(output_folder, f"{scene}_NDSI.tif")

    save_index(savi_path, savi, nir_ds)
    save_index(ndsi_path, ndsi, green_ds)

    print(f"Saved: {savi_path}")
    print(f"Saved: {ndsi_path}")

    # Release datasets and arrays before processing the next scene
    green_ds = red_ds = nir_ds = swir1_ds = None
    green = red = nir = swir1 = None
    savi = ndsi = None

print("\nAll scenes processed successfully!")
