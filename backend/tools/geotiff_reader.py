from pathlib import Path


def read_geotiff(image_path: str):

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {image_path}"
        )

    try:

        import rasterio

    except ImportError:

        return {
            "warning": "rasterio is not installed",
            "filename": path.name,
            "path": str(path)
        }

    with rasterio.open(path) as src:

        return {
            "filename": path.name,
            "width": src.width,
            "height": src.height,
            "bands": src.count,
            "crs": str(src.crs),
            "bounds": {
                "left": src.bounds.left,
                "bottom": src.bounds.bottom,
                "right": src.bounds.right,
                "top": src.bounds.top
            },
            "dtype": str(src.dtypes[0])
        }