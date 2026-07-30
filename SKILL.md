
## Prerequisites / 先准备 X 文件

> ⚠️ **必读** — 本 skill 不属于即用型，需要先准备特定文件才能跑。

本 skill 需要 **红光 + 绿光**两个波段栅格（GeoTIFF）。NIR/SWIR 可选。

👉 完整教程见仓库根目录 `PREREQUISITES.md` 1.8 节。

**先准备 X 文件**：从 Sentinel-2 提取 2-4 个波段，或 `--bbox` 让 skill 自动下载。

快速试跑命令：

```bash
python water_quality_remote_sensing.py --bbox 116,39,117,40 --date-range 2024-06-01,2024-06-30 --output-dir ./wq
```

﻿---
name: water-quality-remote-sensing
description: >
  Estimate water quality parameters from multispectral satellite imagery. Use when the user wants to analyze changes, compare multi-temporal
  rasters, compute indices, or generate assessment reports.
---

# Water Quality Remote Sensing

Estimate water quality parameters from multispectral satellite imagery.

## CLI Usage

```bash
python scripts/water_quality_remote_sensing.py --red red.tif --green green.tif
python scripts/water_quality_remote_sensing.py --red red.tif --green green.tif --nir nir.tif --swir swir.tif
python scripts/water_quality_remote_sensing.py --red red.tif --green green.tif --output-dir my_output
```

## Parameters

| Argument | Required | Default | Description |
|---|---|---|---|
| `--red` | Yes | — | Path to red band raster (≈ 0.6–0.7 μm) |
| `--green` | Yes | — | Path to green band raster (≈ 0.5–0.6 μm) |
| `--nir` | No | — | Optional NIR band raster (≈ 0.8–0.9 μm, enables NDWI / NDVI-based products) |
| `--swir` | No | — | Optional SWIR band raster (≈ 1.6–2.2 μm, enables turbidity proxies) |
| `--output-dir`, `-o` | No | `water-quality-output` | Directory to write outputs |

## Output

| File | Description |
|---|---|
| `water-quality-report.json` | Machine-readable water quality indices |
| `report.html` | Human-readable HTML report |
| `output-manifest.json` | Run metadata + result summary |

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 2 | Argument error (e.g. missing input file) |
| 7 | Processing failure |


## 数据下载

本 skill 可自动从 Microsoft Planetary Computer 下载数据 (无需 API key):

```bash
python water_quality_remote_sensing.py --bbox 116,39,117,40 --date-range 2024-06-01,2024-06-30 --output-dir <tmp>
```

- `--bbox W,S,E,N`: WGS-84 边界框 (西, 南, 东, 北)
- `--date-range START,END`: 日期范围 (YYYY-MM-DD,YYYY-MM-DD)
- `--aoi-file <path.geojson>`: 替代 --bbox 的 GeoJSON 多边形
- `--cache-dir <path>`: 缓存目录 (默认 ~/.geoskill_cache)

当用户只给 `--bbox + --date-range` (没有 `--red`) 时，skill 自动下载数据。
当用户给 `--red` 时，走原文件路径 (向后兼容)。
