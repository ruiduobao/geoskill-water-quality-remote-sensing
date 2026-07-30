#!/usr/bin/env python3
"""
Water Quality Remote Sensing - Estimate water quality parameters from satellite imagery.

Computes turbidity index, chlorophyll-a index, and NDCI from multispectral
imagery for water quality assessment.
"""

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

EXIT_OK = 0
EXIT_ARG = 2
EXIT_PROCESSING = 7


def compute_water_quality(red_path: Path, green_path: Path, nir_path: Path = None,
                          swir_path: Path = None) -> Dict[str, Any]:
    """Compute water quality indices from multispectral bands."""
    try:
        import numpy as np
        import rasterio
    except ImportError:
        return {"error": "rasterio/numpy not available"}

    with rasterio.open(red_path) as ds:
        red = ds.read(1).astype(np.float64)
        transform = ds.transform
        crs = ds.crs
        nodata = ds.nodata
    with rasterio.open(green_path) as ds:
        green = ds.read(1).astype(np.float64)

    if nodata is not None:
        valid = (red != nodata) & (green != nodata)
    else:
        valid = np.ones_like(red, dtype=bool)

    # Water mask (NDWI-like: green - red > 0 for water)
    water = ((green - red) > 0.0) & valid

    # Turbidity Index (TI): higher red reflectance = higher turbidity
    with np.errstate(divide='ignore', invalid='ignore'):
        turbidity = np.where(water, red / np.clip(green, 0.001, None), np.nan)

    # Normalized Difference Turbidity Index (NDTI)
    with np.errstate(divide='ignore', invalid='ignore'):
        ndti = np.where(water, (red - green) / np.clip(red + green, 0.001, None), np.nan)

    # Chlorophyll-a index (Green/Red ratio)
    with np.errstate(divide='ignore', invalid='ignore'):
        chl_index = np.where(water, green / np.clip(red, 0.001, None), np.nan)

    # NDCI (Normalized Difference Chlorophyll Index) if NIR available
    ndci = None
    if nir_path and Path(nir_path).exists():
        with rasterio.open(nir_path) as ds:
            nir = ds.read(1).astype(np.float64)
        with np.errstate(divide='ignore', invalid='ignore'):
            ndci = np.where(water, (nir - red) / np.clip(nir + red, 0.001, None), np.nan)

    # Area
    if crs and crs.is_projected:
        pixel_area = abs(transform.a * transform.e)
    else:
        pixel_area = (abs(transform.a) * 111320) * (abs(transform.e) * 111320)

    water_pixels = int(np.sum(water))

    result = {
        "water_pixels": water_pixels,
        "water_area_km2": round(water_pixels * pixel_area / 1e6, 4),
        "turbidity_mean": round(float(np.nanmean(turbidity[water])), 4) if water_pixels > 0 else None,
        "ndti_mean": round(float(np.nanmean(ndti[water])), 4) if water_pixels > 0 else None,
        "chlorophyll_index_mean": round(float(np.nanmean(chl_index[water])), 4) if water_pixels > 0 else None,
    }
    if ndci is not None:
        result["ndci_mean"] = round(float(np.nanmean(ndci[water])), 4) if water_pixels > 0 else None

    return result


def generate_report(result: Dict, output_dir: Path) -> None:
    now = datetime.now(timezone.utc).isoformat()
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>Water Quality Report</title>
<style>
body{{font-family:sans-serif;max-width:900px;margin:20px auto;padding:0 20px}}
h1{{color:#1a237e}}.summary{{background:#e0f7fa;padding:15px;border-radius:8px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #b2ebf2;padding:8px;text-align:left}}
th{{background:#b2ebf2}}
</style></head>
<body>
<h1>Water Quality Remote Sensing Report</h1>
<p>Generated: {now}</p>
<div class="summary">
<table>
<tr><td>Water area</td><td><strong>{result.get('water_area_km2', 0)} km²</strong></td></tr>
<tr><td>Turbidity (mean)</td><td><strong>{result.get('turbidity_mean', 'N/A')}</strong></td></tr>
<tr><td>NDTI (mean)</td><td><strong>{result.get('ndti_mean', 'N/A')}</strong></td></tr>
<tr><td>Chlorophyll index</td><td><strong>{result.get('chlorophyll_index_mean', 'N/A')}</strong></td></tr>
</table>
</div>
</body></html>"""
    (output_dir / "report.html").write_text(html, encoding="utf-8")
    (output_dir / "water-quality-report.json").write_text(
        json.dumps({"timestamp": now, "results": result}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def run_water_quality(args: argparse.Namespace) -> int:
    for p, name in [(Path(args.red), "Red"), (Path(args.green), "Green")]:
        if not p.exists():
            print(f"ERROR: {name} band not found: {p}", file=sys.stderr)
            return EXIT_ARG

    output_dir = Path(args.output_dir) if args.output_dir else Path("water-quality-output")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Computing water quality indices...")
    result = compute_water_quality(
        Path(args.red), Path(args.green),
        Path(args.nir) if args.nir else None,
        Path(args.swir) if args.swir else None,
    )
    print(f"  Water area: {result.get('water_area_km2', 0)} km²")

    generate_report(result, output_dir)
    manifest = {"timestamp": datetime.now(timezone.utc).isoformat(), "results": result}
    (output_dir / "output-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Output: {output_dir}")
    return EXIT_OK


def main():
    parser = argparse.ArgumentParser(description="Water Quality Remote Sensing")
    parser.add_argument("--red", required=True, help="Red band raster")
    parser.add_argument("--green", required=True, help="Green band raster")
    parser.add_argument("--nir", help="NIR band raster (optional)")
    parser.add_argument("--swir", help="SWIR band raster (optional)")
    parser.add_argument("--output-dir", "-o", help="Output directory")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    args = parser.parse_args()
    try:
        sys.exit(run_water_quality(args))
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_PROCESSING)


if __name__ == "__main__":
    main()
