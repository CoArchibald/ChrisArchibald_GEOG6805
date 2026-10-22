
import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask

# --------------------------------------------------
# 1. Paths and scene settings
# --------------------------------------------------
script_folder = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_folder, "../.."))

input_folder = os.path.join(project_root, "Input")
output_folder = os.path.join(script_folder, "Output")
training_file = os.path.join(script_folder, "training_areas.gpkg")

os.makedirs(output_folder, exist_ok=True)

# Reference scene: less cloud cover
reference_scene = "LT50290372010217EDC00"

# Target scene: normalize to match the reference
target_scene = "LT50290372010233EDC00"

# Landsat 5 bands
bands = ["B3", "B4", "B5"]


# --------------------------------------------------
# 2. Load training polygons
# --------------------------------------------------
training_areas = gpd.read_file(training_file)
training_areas["type"] = training_areas["type"].str.lower()

required_types = {"dark", "bright"}
found_types = set(training_areas["type"])

if not required_types.issubset(found_types):
    raise ValueError(
        "Training polygons must be labeled 'dark' and 'bright'."
    )


# --------------------------------------------------
# 3. Build raster file paths
# --------------------------------------------------
def band_path(scene, band):
    return os.path.join(
        input_folder,
        scene,
        f"{scene}_{band}.TIF"
    )


# --------------------------------------------------
# 4. Calculate mean pixel value inside a polygon
# --------------------------------------------------
def polygon_mean(raster_path, polygon):
    with rasterio.open(raster_path) as src:
        polygon_in_raster_crs = polygon.to_crs(src.crs)

        geometries = [
            feature.__geo_interface__
            for feature in polygon_in_raster_crs.geometry
        ]

        data, _ = mask(
            src,
            geometries,
            crop=True,
            filled=False
        )

        values = data[0].compressed()

        if values.size == 0:
            raise ValueError(
                f"No valid pixels found in {raster_path}"
            )

        return float(np.mean(values))


# --------------------------------------------------
# 5. Calculate normalization coefficients and
#    normalize each target band
# --------------------------------------------------
for band in bands:
    reference_path = band_path(reference_scene, band)
    target_path = band_path(target_scene, band)

    means = {}

    for area_type in ["dark", "bright"]:
        polygon = training_areas[
            training_areas["type"] == area_type
        ]

        means[(reference_scene, area_type)] = polygon_mean(
            reference_path, polygon
        )

        means[(target_scene, area_type)] = polygon_mean(
            target_path, polygon
        )

    # Reference DN = slope * Target DN + intercept
    target_dark = means[(target_scene, "dark")]
    target_bright = means[(target_scene, "bright")]

    reference_dark = means[(reference_scene, "dark")]
    reference_bright = means[(reference_scene, "bright")]

    if np.isclose(target_bright, target_dark):
        raise ValueError(
            f"Dark and bright means are too similar in {band}."
        )

    slope = (
        (reference_bright - reference_dark)
        / (target_bright - target_dark)
    )

    intercept = reference_dark - slope * target_dark

    print(f"\nBand {band}")
    print(f"  Reference dark mean:   {reference_dark:.3f}")
    print(f"  Target dark mean:      {target_dark:.3f}")
    print(f"  Reference bright mean: {reference_bright:.3f}")
    print(f"  Target bright mean:    {target_bright:.3f}")
    print(f"  Slope:                 {slope:.6f}")
    print(f"  Intercept:             {intercept:.6f}")

    # Output file
    output_path = os.path.join(
        output_folder,
        f"{target_scene}_{band}_normalized.tif"
    )

    # Save as float32 to preserve decimal values
    with rasterio.open(target_path) as src:
        profile = src.profile.copy()
        profile.update(dtype="float32", count=1)

        nodata = src.nodata

        with rasterio.open(
            output_path,
            "w",
            **profile
        ) as dst:

            for _, window in src.block_windows(1):
                data = src.read(1, window=window)

                valid = np.ones(data.shape, dtype=bool)

                if nodata is not None:
                    valid &= data != nodata

                corrected = data.astype(np.float32)

                corrected[valid] = (
                    slope * corrected[valid] + intercept
                )

                dst.write(corrected, 1, window=window)


print("\nNormalization complete!")
print(f"Normalized rasters saved to: {output_folder}")


# --------------------------------------------------
# 6. Verify normalized dark and bright means
# --------------------------------------------------
print("\nVerification of normalized rasters:")

for band in bands:
    reference_path = band_path(reference_scene, band)

    normalized_path = os.path.join(
        output_folder,
        f"{target_scene}_{band}_normalized.tif"
    )

    for area_type in ["dark", "bright"]:
        polygon = training_areas[
            training_areas["type"] == area_type
        ]

        reference_mean = polygon_mean(
            reference_path, polygon
        )

        normalized_mean = polygon_mean(
            normalized_path, polygon
        )

        print(
            f"{band} {area_type}: "
            f"reference={reference_mean:.3f}, "
            f"normalized={normalized_mean:.3f}"
        )

print("\nAssignment 2 processing finished successfully!")
