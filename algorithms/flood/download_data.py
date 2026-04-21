import warnings
warnings.filterwarnings("ignore")

import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
import numpy as np
import os
import zipfile
import requests
import geopandas as gpd


# -------------------------
# Config
# -------------------------
CFG = {
    "study_area_shp": "study_area.shp",
    "dem_tif": "dem.tif",

    "data_dir": "data",
    "raw_dir": "data/raw",
    "proc_dir": "data/processed",

    # Your bbox (EPSG:4326)
    "north": 39.861329,
    "south": 38.202345,
    "west": 69.219977,
    "east": 73.704541,

    # ERA5-Land time selection (example: one month)
    "era5_year": "2018",
    "era5_month": "10",
}

# 用 os.makedirs 创建 raw（存放原始下载数据）和 processed（存放对齐后的数据）文件夹。
os.makedirs(CFG["raw_dir"], exist_ok=True)
os.makedirs(CFG["proc_dir"], exist_ok=True)

# 根据study_area.shp 矢量边界，把巨大的原始影像切成仅包含流域部分的形状。
def clip_to_study_area(in_raster, study_gdf, out_raster):
    with rasterio.open(in_raster) as src:
        geom = [study_gdf.to_crs(src.crs).unary_union.__geo_interface__]
        out_img, out_transform = mask(src, geom, crop=True)
        out_meta = src.meta.copy()
        out_meta.update({
            "height": out_img.shape[1],
            "width": out_img.shape[2],
            "transform": out_transform
        })
        with rasterio.open(out_raster, "w", **out_meta) as dst:
            dst.write(out_img)
    return out_raster

# 以 DEM 为基准，强行要求其他数据（如降雨量、土地利用）的行数、列数、坐标系和空间分辨率与其完全一致。
def match_dem_grid(src_tif, dem_tif, out_tif, resampling=Resampling.bilinear):
    """Reproject/resample src_tif to match DEM's crs/transform/shape.
       Force float32 output and NaN nodata to avoid 'all zeros' issues.
    """
    with rasterio.open(dem_tif) as dem:
        dst_crs = dem.crs
        dst_transform = dem.transform
        dst_height = dem.height
        dst_width = dem.width

        # 关键：不要直接用 dem.profile（会带入整型 dtype 和 nodata=32767）
        dst_profile = dem.profile.copy()
        dst_profile.update({
            "driver": "GTiff",
            "crs": dst_crs,
            "transform": dst_transform,
            "height": dst_height,
            "width": dst_width,
            "count": 1,
            "dtype": "float32",     # 关键：强制 float
            "nodata": np.nan,       # 关键：nodata 用 NaN
            "compress": "LZW"
        })

    with rasterio.open(src_tif) as src:
        src_nodata = src.nodata

        dst_data = np.full((dst_height, dst_width), np.nan, dtype=np.float32)

        reproject(
            source=rasterio.band(src, 1),
            destination=dst_data,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src_nodata,     # 关键：告诉 reproject 源nodata
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=np.nan,         # 关键：目标 nodata
            resampling=resampling,
        )

    with rasterio.open(out_tif, "w", **dst_profile) as dst:
        dst.write(dst_data, 1)

    return out_tif

# 下载 total_precipitation（总降水量）和 volumetric_soil_water_layer_1（第一层土壤水分）
def download_era5_land_nc(out_nc):
    """
    Download ERA5-Land for bbox using CDS API.
    Requires ~/.cdsapirc configured.
    """
    import cdsapi

    c = cdsapi.Client()
    days = [f"{d:02d}" for d in range(1, 32)]
    hours = [f"{h:02d}:00" for h in range(0, 24)]

    # CDS area: [north, west, south, east]
    area = [CFG["north"], CFG["west"], CFG["south"], CFG["east"]]

    req = {
        "variable": [
            "total_precipitation",
            "volumetric_soil_water_layer_1"
        ],
        "year": CFG["era5_year"],
        "month": CFG["era5_month"],
        "day": days,
        "time": hours,
        "area": area,
        "format": "netcdf",
    }

    print("[ERA5-Land] Downloading netCDF...")
    c.retrieve("reanalysis-era5-land", req, out_nc)
    print("[ERA5-Land] Saved:", out_nc)
    return out_nc

# 将下载的 .nc 格式（气象常用）转换为常用的 .tif 格式，并将每小时的数据累加/平均为月度数据。
def era5_nc_to_geotiff(era5_zip_path, out_tp_tif, out_swvl1_tif):
    import os
    import zipfile
    import xarray as xr
    import rioxarray  # noqa

    # 1) unzip
    extract_dir = os.path.splitext(era5_zip_path)[0] + "_unzipped"
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(era5_zip_path, "r") as z:
        z.extractall(extract_dir)

    # 2) find netcdf inside
    nc_files = []
    for root, _, files in os.walk(extract_dir):
        for fn in files:
            if fn.lower().endswith(".nc"):
                nc_files.append(os.path.join(root, fn))

    if not nc_files:
        raise RuntimeError(f"No .nc found inside ZIP: {era5_zip_path}")

    nc_path = nc_files[0]
    print("[ERA5] Extracted NetCDF:", nc_path)

    # 3) open netcdf explicitly with netcdf4 engine
    ds = xr.open_dataset(nc_path, engine="netcdf4")
    print("[ERA5] Variables:", list(ds.data_vars.keys()))

    # 4) compute monthly aggregates
    # 自动识别时间维度
    time_dim = None
    for d in ds.dims:
        if "time" in d:
            time_dim = d
            break

    print("Time dimension:", time_dim)

    # tp: meters -> monthly sum -> mm
    tp = ds["tp"].sum(dim=time_dim) * 1000.0

    # soil moisture: monthly mean
    swvl1 = ds["swvl1"].mean(dim=time_dim)

    # 5) write GeoTIFF in EPSG:4326
    def _to_tif(da, out_path):
        if "latitude" in da.dims and "longitude" in da.dims:
            da = da.rename({"latitude": "y", "longitude": "x"})
        elif "lat" in da.dims and "lon" in da.dims:
            da = da.rename({"lat": "y", "lon": "x"})
        if da["y"][0] < da["y"][-1]:
            da = da.sortby("y", ascending=False)
        da = da.astype("float32")
        da.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
        da.rio.write_crs("EPSG:4326", inplace=True)
        da.rio.to_raster(out_path)

    _to_tif(tp, out_tp_tif)
    _to_tif(swvl1, out_swvl1_tif)

    print("[ERA5] GeoTIFF saved:")
    print("  -", out_tp_tif)
    print("  -", out_swvl1_tif)

# 微软的 Planetary Computer 获取 ESA 的 10 米分辨率全球土地覆盖数据
def _resolve_era5_nc_path(era5_source_path):
    import os
    import zipfile

    if not os.path.exists(era5_source_path):
        raise FileNotFoundError(f"ERA5 source not found: {era5_source_path}")

    if era5_source_path.lower().endswith(".nc"):
        return era5_source_path

    if not era5_source_path.lower().endswith(".zip"):
        raise ValueError(f"Unsupported ERA5 file format: {era5_source_path}")

    extract_dir = os.path.splitext(era5_source_path)[0] + "_unzipped"
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(era5_source_path, "r") as z:
        z.extractall(extract_dir)

    nc_files = []
    for root, _, files in os.walk(extract_dir):
        for fn in files:
            if fn.lower().endswith(".nc"):
                nc_files.append(os.path.join(root, fn))

    if not nc_files:
        raise RuntimeError(f"No .nc found in ERA5 archive: {era5_source_path}")

    return nc_files[0]


def _find_time_dim(ds):
    for dim_name in ds.dims:
        if "time" in dim_name.lower():
            return dim_name
    raise RuntimeError("Could not find ERA5 time dimension.")


def _write_dataarray_tif(da, out_path):
    import rioxarray  # noqa

    if "latitude" in da.dims and "longitude" in da.dims:
        da = da.rename({"latitude": "y", "longitude": "x"})
    elif "lat" in da.dims and "lon" in da.dims:
        da = da.rename({"lat": "y", "lon": "x"})

    if da["y"][0] < da["y"][-1]:
        da = da.sortby("y", ascending=False)

    da = da.astype("float32")
    da.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
    da.rio.write_crs("EPSG:4326", inplace=True)
    da.rio.to_raster(out_path)


def era5_nc_to_daily_geotiffs(era5_source_path, out_dir):
    import numpy as np
    import xarray as xr

    os.makedirs(out_dir, exist_ok=True)

    nc_path = _resolve_era5_nc_path(era5_source_path)
    print("[ERA5] Using NetCDF:", nc_path)

    ds = xr.open_dataset(nc_path, engine="netcdf4")
    time_dim = _find_time_dim(ds)

    tp_daily = ds["tp"].resample({time_dim: "1D"}).sum() * 1000.0
    swvl1_daily = ds["swvl1"].resample({time_dim: "1D"}).mean()

    outputs = {
        "rain_raw_files": [],
        "soil_raw_files": [],
    }

    for timestamp in tp_daily[time_dim].values:
        date_str = np.datetime_as_string(timestamp, unit="D")
        compact_date = date_str.replace("-", "")

        rain_out = os.path.join(out_dir, f"era5_tp_mm_{compact_date}.tif")
        soil_out = os.path.join(out_dir, f"era5_swvl1_mean_{compact_date}.tif")

        if not os.path.exists(rain_out):
            _write_dataarray_tif(tp_daily.sel({time_dim: timestamp}), rain_out)
        if not os.path.exists(soil_out):
            _write_dataarray_tif(swvl1_daily.sel({time_dim: timestamp}), soil_out)

        outputs["rain_raw_files"].append(rain_out)
        outputs["soil_raw_files"].append(soil_out)

    print(f"[ERA5] Daily GeoTIFF count: {len(outputs['rain_raw_files'])}")
    return outputs


def _extract_daily_token(path):
    name = os.path.basename(path)
    digits = "".join(ch for ch in name if ch.isdigit())
    for idx in range(len(digits) - 7):
        token = digits[idx:idx + 8]
        if token.startswith("20"):
            return f"{token[:4]}-{token[4:6]}-{token[6:8]}"
    raise ValueError(f"Could not extract date from file name: {path}")


def match_daily_era5_to_dem_grid(rain_raw_files, soil_raw_files, dem_tif, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    outputs = {
        "rain_daily_files": [],
        "soil_daily_files": [],
    }

    for raw_path in rain_raw_files:
        date_token = _extract_daily_token(raw_path)
        out_path = os.path.join(out_dir, f"rain_mm_demgrid_{date_token}.tif")
        if not os.path.exists(out_path):
            match_dem_grid(raw_path, dem_tif, out_path, resampling=Resampling.bilinear)
            print("[ERA5] Matched rainfall to DEM grid:", out_path)
        outputs["rain_daily_files"].append(out_path)

    for raw_path in soil_raw_files:
        date_token = _extract_daily_token(raw_path)
        out_path = os.path.join(out_dir, f"soil_moist_demgrid_{date_token}.tif")
        if not os.path.exists(out_path):
            match_dem_grid(raw_path, dem_tif, out_path, resampling=Resampling.bilinear)
            print("[ERA5] Matched soil moisture to DEM grid:", out_path)
        outputs["soil_daily_files"].append(out_path)

    return outputs


def download_worldcover_to_demgrid(dem_tif, out_tif):
    """
    Download ESA WorldCover tiles from Planetary Computer and directly resample/reproject
    into the DEM grid (very low memory, no stackstac).

    Output:
      - GeoTIFF aligned to dem_tif (same CRS/transform/shape)
      - dtype uint8, nodata=0
    """
    import numpy as np
    import rasterio
    from rasterio.warp import reproject, Resampling
    from pystac_client import Client
    import planetary_computer as pc

    # bbox: [minx, miny, maxx, maxy] in EPSG:4326
    bbox = [CFG["west"], CFG["south"], CFG["east"], CFG["north"]]

    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

    # Prefer 2021, fallback all-time
    search = catalog.search(
        collections=["esa-worldcover"],
        bbox=bbox,
        datetime="2021-01-01/2021-12-31",
        max_items=500
    )
    items = list(search.get_items())
    if not items:
        print("[WorldCover] No 2021 items; falling back to all-time search...")
        search = catalog.search(
            collections=["esa-worldcover"],
            bbox=bbox,
            max_items=500
        )
        items = list(search.get_items())

    if not items:
        raise RuntimeError("No ESA WorldCover items found for bbox on Planetary Computer.")

    # Target grid = DEM grid
    with rasterio.open(dem_tif) as dem:
        dst_crs = dem.crs
        dst_transform = dem.transform
        dst_h, dst_w = dem.height, dem.width
        dst_profile = dem.profile.copy()
        dst_profile.update(
            driver="GTiff",
            count=1,
            dtype="uint8",
            nodata=0,
            compress="LZW"
        )

    # Destination landcover (0 = nodata)
    dst = np.zeros((dst_h, dst_w), dtype=np.uint8)

    # Reproject each tile onto DEM grid and mosaic (only fill where dst==0)
    print(f"[WorldCover] Found {len(items)} tile item(s). Reprojecting to DEM grid...")
    for it in items:
        it = pc.sign(it)
        if "map" not in it.assets:
            continue

        href = it.assets["map"].href

        try:
            with rasterio.open(href) as src:
                tmp = np.zeros((dst_h, dst_w), dtype=np.uint8)

                reproject(
                    source=rasterio.band(src, 1),
                    destination=tmp,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src.nodata if src.nodata is not None else 0,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    dst_nodata=0,
                    resampling=Resampling.nearest,  # categorical
                )

                # Mosaic: write new pixels where dst is nodata and tmp has data
                mask = (dst == 0) & (tmp != 0)
                if np.any(mask):
                    dst[mask] = tmp[mask]

        except Exception as e:
            print(f"[WorldCover] Skip tile {it.id} due to error: {e}")

    # Save
    with rasterio.open(out_tif, "w", **dst_profile) as out:
        out.write(dst, 1)

    print("[WorldCover] Saved DEM-grid landcover:", out_tif)

# 使用 osmnx 直接抓取 OpenStreetMap 里的河流线（Waterway）。离河流的距离通常是洪涝预测的重要特征。
import osmnx as ox

def download_osm_rivers(study_gdf, out_gpkg):
    """
    Faster OSM waterway download:
    - query by polygon (smaller than bbox)
    - restrict tags to river/stream
    """
    poly = study_gdf.to_crs(4326).unary_union
    tags = {"waterway": ["river", "stream"]}

    print("[OSM] Downloading waterways (river/stream) by polygon...")
    try:
        gdf = ox.features_from_polygon(poly, tags=tags)
    except AttributeError:
        # fallback if older osmnx
        gdf = ox.geometries_from_polygon(poly, tags=tags)

    if gdf.empty:
        raise RuntimeError("No OSM waterway features found in study area.")

    gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])].copy()
    gdf = gdf.to_crs(4326)

    gdf.to_file(out_gpkg, layer="waterways", driver="GPKG")
    print("[OSM] Saved:", out_gpkg)


def download_hydrorivers(study_gdf, out_gpkg):
    """
    Download HydroRIVERS dataset and clip to study area.
    """

    url = "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10.gdb.zip"
    zip_path = os.path.join(CFG["raw_dir"], "hydrorivers.zip")
    extract_dir = os.path.join(CFG["raw_dir"], "hydrorivers")

    if not os.path.exists(zip_path):
        print("[HydroRIVERS] Downloading...")
        r = requests.get(url, stream=True)
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        print("[HydroRIVERS] Downloaded.")

    if not os.path.exists(extract_dir):
        print("[HydroRIVERS] Extracting...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)

    print("[HydroRIVERS] Loading dataset...")

    # 找到 gdb 文件
    gdb_path = None
    for root, dirs, files in os.walk(extract_dir):
        for d in dirs:
            if d.endswith(".gdb"):
                gdb_path = os.path.join(root, d)

    if gdb_path is None:
        raise RuntimeError("HydroRIVERS gdb not found.")

    rivers = gpd.read_file(gdb_path, layer="HydroRIVERS_v10")

    # 投影统一
    rivers = rivers.to_crs(4326)

    # 裁剪到研究区
    rivers_clip = gpd.clip(rivers, study_gdf)

    rivers_clip.to_file(out_gpkg, driver="GPKG")

    print("[HydroRIVERS] Saved:", out_gpkg)

def raster_stats(path):
    import rasterio
    import numpy as np
    with rasterio.open(path) as src:
        a = src.read(1).astype("float32")
        nd = src.nodata
        if nd is not None and np.isfinite(nd):
            a[a == nd] = np.nan
        return {
            "path": path,
            "dtype": src.dtypes[0],
            "nodata": src.nodata,
            "min": float(np.nanmin(a)),
            "max": float(np.nanmax(a)),
            "nan_pct": float(np.isnan(a).mean() * 100),
        }

def main():
    study = gpd.read_file(CFG["study_area_shp"]).to_crs(4326)

    # Clip DEM to study area (optional but recommended)
    dem_clip = os.path.join(CFG["proc_dir"], "dem_clip.tif")
    if not os.path.exists(dem_clip):
        clip_to_study_area(CFG["dem_tif"], study, dem_clip)
        print("[DEM] Clipped:", dem_clip)

    # ERA5-Land
    era5_nc = os.path.join(CFG["raw_dir"], f"era5_land_{CFG['era5_year']}{CFG['era5_month']}.nc")
    if not os.path.exists(era5_nc):
        download_era5_land_nc(era5_nc)

    raw_daily_dir = os.path.join(CFG["raw_dir"], "daily")
    proc_daily_dir = os.path.join(CFG["proc_dir"], "daily")
    daily_raw_outputs = era5_nc_to_daily_geotiffs(era5_nc, raw_daily_dir)
    daily_proc_outputs = match_daily_era5_to_dem_grid(
        daily_raw_outputs["rain_raw_files"],
        daily_raw_outputs["soil_raw_files"],
        dem_clip,
        proc_daily_dir,
    )

    # WorldCover landuse
    wc_tif = os.path.join(CFG["proc_dir"], "landcover_demgrid.tif")
    if not os.path.exists(wc_tif):
        download_worldcover_to_demgrid(dem_clip, wc_tif)

    # OSM rivers
    # rivers_gpkg = os.path.join(CFG["raw_dir"], "osm_waterways.gpkg")
    # if not os.path.exists(rivers_gpkg):
    #     download_osm_rivers(study, rivers_gpkg)
    rivers_gpkg = os.path.join(CFG["raw_dir"], "hydrorivers.gpkg")
    if not os.path.exists(rivers_gpkg):
        download_hydrorivers(study, rivers_gpkg)

    print("\nAll data prepared in:", CFG["proc_dir"])
    if daily_raw_outputs["soil_raw_files"]:
        print(raster_stats(daily_raw_outputs["soil_raw_files"][0]))
    if daily_proc_outputs["soil_daily_files"]:
        print(raster_stats(daily_proc_outputs["soil_daily_files"][0]))


if __name__ == "__main__":
    main()
