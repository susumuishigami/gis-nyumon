# ## 行政区域データの取得（片品村）
#
# ### データ
# 国土数値情報（行政区域データ）
#
# ファイル名:
#     N03-20250101_10.geojson
#
# ### 入手方法
#
# 1. 国土数値情報ダウンロードページにアクセス
#    https://nlftp.mlit.go.jp/ksj/
#
# 2. 「行政区域データ（N03）」を選択
#
# 3. 最新版（例: 2025年版）をダウンロード
#
# 4. 解凍して以下のファイルを使用
#    N03-20250101_10.geojson
#
# 5. プロジェクトルートに配置

import geopandas as gpd
import matplotlib.pyplot as plt

# 地理院市区町村界データを取得し、片品村をプロット

gdf = gpd.read_file("input/N03-20250101_10.geojson")

katashina = gdf[gdf["N03_004"] == "片品村"]

katashina.plot(edgecolor="black", figsize=(6, 6))
plt.title("area of Katashina village")

# 片品村の重心を計算

katashina_proj = katashina.to_crs(epsg=3099)  # EPSG: 3099 is UTM zone 53N for Japan 東経132-138
centroid = katashina_proj.geometry.centroid
bbox = katashina_proj.total_bounds
xmin, ymin, xmax, ymax = bbox
xs = [xmin, xmax, xmax, xmin, xmin]
ys = [ymin, ymin, ymax, ymax, ymin]

[centroid, xmin, ymin, xmax, ymax, xs, ys]  # Show centroid and bounding box coordinates EPSG:3099 なので、単位はメートル

# グラフ描画

fig, ax = plt.subplots(figsize=(6, 6))
katashina_proj.plot(ax=ax, color="lightgray", edgecolor="black")
centroid.plot(ax=ax, color="red", markersize=40)

ax.plot(xs, ys, color="blue")
plt.title("Katashina village: centroid and bounding box")


# ## 片品村のDEMタイルを地理院から取得

# ### 使用データ
# 地理院タイル（標高PNG）
#
# ベースURL:
#
#     https://cyberjapandata.gsi.go.jp/xyz/dem_png/{z}/{x}/{y}.png
#
# ### 使用仕様
# - 座標系: JGD2011（緯度経度）
# - タイルサイズ: 256 x 256 px
# - Z=14（DEM10B相当）

# まずは緯度経度範囲を取得

katashina.total_bounds

lon_min, lon_max = 139.13910039, 139.40670927
lat_min, lat_max = 36.70963233, 36.96452192

# ## タイル座標の取得方法
#
# 片品村の範囲（JGD2011）
#
#     lon_min = 139.13910039
#     lat_min = 36.70963233
#     lon_max = 139.40670927
#     lat_max = 36.96452192
#
# これをもとに、XYZタイル座標へ変換する必要があり。
#
# 変換式（Web Mercator）:
#
#     n = 2^z
#     xtile = int((lon + 180) / 360 * n)
#
#     lat_rad = radians(lat)
#     ytile = int((1 - log(tan(lat_rad) + 1/cos(lat_rad)) / pi) / 2 * n)
#
# この範囲内の x, y を全て取得。
#
# 参考: https://maps.gsi.go.jp/development/siyou.html

import math


def lonlat_to_tile(lon, lat, z):
    lat_rad = math.radians(lat)
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return x, y


def tile_to_lonlat(x, y, z):
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lon, lat


# 今回はZ=14（DEM10B: 1/2.5万地形図等高線）の最大を採用
# https://maps.gsi.go.jp/development/hyokochi.html

x_min, y_min = lonlat_to_tile(lon_min, lat_max, 14)  # (x_min, y_min)
x_min, y_min

x_max, y_max = lonlat_to_tile(lon_max, lat_min, 14)  # (x_max, y_max)
x_max, y_max

# URL一覧を生成

urls = []
for x in range(x_min, x_max + 1):
    for y in range(y_min, y_max + 1):
        urls.append(f"https://cyberjapandata.gsi.go.jp/xyz/dem_png/14/{x}/{y}.png")
urls

len(urls)

# 地理院のサイトからダウンロード

import requests

import time
from pathlib import Path

for url in urls:
    response = requests.get(
        url,
        headers={"User-Agent": "downloader by susumuis (for personal GIS research)"}
    )
    filename = url.split("/")[-3] + "_" + url.split("/")[-2] + "_" + url.split("/")[-1]
    with open(Path("output") / filename, "wb") as f:
        f.write(response.content)
    time.sleep(0.1)

# ## タイルの結合
#
# Pillow を使用して1枚画像に結合
#
# - 横方向: x昇順
# - 縦方向: y昇順（上→下）

from pathlib import Path
from PIL import Image

tiles_dir = Path("output")
z = 14

# どんな画像か確認

sample_path = tiles_dir / f"{z}_{x_min}_{y_min}.png"
sample_img = Image.open(sample_path)
tile_width, tile_height = sample_img.size
mode = sample_img.mode
print("tile size:", tile_width, tile_height, "mode:", mode)

# 全体のサイズを計算

nx = x_max - x_min + 1  # 横方向のタイル数
ny = y_max - y_min + 1  # 縦方向のタイル数

merged_width = nx * tile_width
merged_height = ny * tile_height

print("merged size:", merged_width, merged_height)

# 画像を結合して保存

merged = Image.new(mode, (merged_width, merged_height))
# 上から下へ（y_min が最北 → 画像の一番上）
for j, y in enumerate(range(y_min, y_max + 1)):
    for i, x in enumerate(range(x_min, x_max + 1)):
        tile_path = tiles_dir / f"{z}_{x}_{y}.png"
        tile = Image.open(tile_path)

        # 貼り付け位置（左上座標）
        px = i * tile_width
        py = j * tile_height

        merged.paste(tile, (px, py))

# 保存
out_path = Path("katashina_dem_z14_merged.png")
merged.save(out_path)
print("saved:", out_path)

# タイルXY番号を緯度経度に変換

# 左上タイル (x_min, y_min) の左上角
lon_ul, lat_ul = tile_to_lonlat(x_min, y_min, z)

# 右下タイル (x_max+1, y_max+1) の右下角
lon_lr, lat_lr = tile_to_lonlat(x_max + 1, y_max + 1, z)

print("upper-left:", lon_ul, lat_ul)
print("lower-right:", lon_lr, lat_lr)

# ## 8. GeoTIFF化（ジオリファレンス付与）
#
# GDALを使用
#
#     gdal_translate \
#       -of GTiff \
#       -a_ullr <lon_min> <lat_max> <lon_max> <lat_min> \
#       -a_srs EPSG:4326 \
#       katashina_dem_z14_merged.png katashina_dem_z14_georef.tif
#
# ※ タイル境界に合わせた座標を使用する

print(rf"""gdal_translate \
  -of GTiff \
  -a_ullr {lon_ul} {lat_ul} {lon_lr} {lat_lr} \
  -a_srs EPSG:4326 \
  katashina_dem_z14_merged.png katashina_dem_z14_georef.tif
""")

# 早速DEMを展開しよう

import rioxarray as rxr
import numpy as np

# 標高タイル（xyz形式）読み込み
dem = rxr.open_rasterio("output/katashina_dem_z14_georef.tif")

# 勾配計算
dy, dx = np.gradient(dem[0])
slope = np.sqrt(dx ** 2 + dy ** 2)

plt.imshow(slope, cmap="terrain")
plt.title("Slope from DEM of Katashina village")
plt.colorbar()

# 違和感がある。
#
# どうやら、EPSG: 4326のままで購買計算をしたからのようだ。
# 以下のコマンドで EPSG: 3099 に変換する。
#
# ```console
# $ gdalwarp \
#   -t_srs EPSG:3099 \
#   -r bilinear \
#   katashina_dem_z14_georef.tif \
#   katashina_dem_z14_proj.tif
# ```
#
# そのうえで再度チャレンジ

# 標高タイル（xyz形式）読み込み
dem = rxr.open_rasterio("output/katashina_dem_z14_proj.tif")

h = dem[0]

# geotransform からピクセルサイズを取得
res_y, res_x = dem.rio.resolution()
res_x = abs(res_x)
res_y = abs(res_y)

dy, dx = np.gradient(h)
slope = np.sqrt((dx / res_x) ** 2 + (dy / res_y) ** 2)

plt.imshow(slope, cmap="terrain")
plt.title("Slope from DEM of Katashina village (Projected)")
plt.colorbar()
