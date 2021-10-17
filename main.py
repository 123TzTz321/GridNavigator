import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
#plt.rcParams['toolbar'] = 'None'
import csv
import urllib.request

from geopy import Point
from geopy.distance import geodesic
import math
import threading
import gpsd
import os
import config
import time


class Map():
    def __init__(self,BaseURL,token=''):
        print("init Map")
        self.BaseURL=BaseURL
        self.token=token
        self.tileSet=[]
    def get_tile(self, xtile, ytile, zoom):
        if self.BaseURL:
            if token:
                TileURL = f"{self.BaseURL}{zoom}/{xtile}/{ytile}.jpg90?access_token={token}"
            else:
                TileURL = f"{self.BaseURL}{zoom}/{xtile}/{ytile}.png"
        else:
            TileURL=f"http://a.tile.openstreetmap.org/{zoom}/{xtile}/{ytile}.png"
        print(TileURL)
        fileName = os.path.join('tiles', f"{xtile}_{ytile}_{zoom}.jpg")
        headers = {'User-Agent': 'PythonMap_agent'}
        req = urllib.request.Request(TileURL, headers=headers)
        f = urllib.request.urlopen(req)
        tile_image = plt.imread(f, format='jpeg')
        plt.imsave(fileName, tile_image)
        return tile_image

    def add_tile(self, xtile, ytile, zoom):
        tile_image = None
        fileName = os.path.join('tiles', f"{xtile}_{ytile}_{zoom}.jpg")
        try:
            if os.path.isfile(fileName):
                print(f"Found {fileName} in cache")
                tile_image = plt.imread(fileName, format='jpeg', )
            elif os.path.isfile(f"{fileName}.lock"):
                print(f"still downloading {fileName}")
            else:
                tile_image = self.get_tile(xtile, ytile, zoom)
        except Exception as e:
            print(e)
            print(f"delete broken{fileName}")
            os.remove(fileName)

        tile = [xtile, ytile, zoom, tile_image]
        self.tileSet.append(tile)

    def clear_tile_list(self):
        self.tileSet=[]

    def get_tilSet(self):
        return self.tileSet


def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)


def meter2deg(pos, m_error):
    A = Point(geodesic(meters=m_error).destination(pos, 0).format_decimal())
    B = Point(geodesic(meters=m_error).destination(pos, 90).format_decimal())
    C = Point(geodesic(meters=m_error).destination(pos, 180).format_decimal())
    D = Point(geodesic(meters=m_error).destination(pos, 270).format_decimal())

    lat_error=abs(B.longitude-D.longitude)
    lon_error=abs(A.latitude-C.latitude)
    return  lat_error,lon_error

def plotTile(xtile, ytile,zoom,plt,mapmgr):
    print(f"x{xtile}\t\ty:{ytile}\t\tzoom{zoom}")
    tile=None
    fileName = os.path.join('tiles', f"{xtile}_{ytile}_{zoom}.jpg")
    try:
        if os.path.isfile(fileName):
            print(f"Found {fileName}")
            tile = plt.imread(fileName, format='jpeg',)
        else:
           tile = mapmgr.get_tile(xtile, ytile,zoom,token=token)
    except Exception as e:
        print(e)
        os.remove(fileName)

    if tile is not None:
        (tile_latitude, tile_longitude) = num2deg(xtile, ytile, zoom=zoom)
        (la1, lo1) = num2deg(xtile + 1, ytile + 1, zoom=zoom)
        plt.imshow(tile, extent=[tile_longitude, lo1, la1, tile_latitude])

def plotTileList(tilset):
    for tile in tilset:
        (tile_latitude, tile_longitude) = num2deg(tile[0], tile[1], zoom=tile[2])
        (la1, lo1) = num2deg(tile[0] + 1, tile[1] + 1, zoom=tile[2])
        plt.imshow(tile[3], extent=[tile_longitude, lo1, la1, tile_latitude])

def generateGrid(pos,length,width,angle):
    print("todo")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    gpsd.connect('raspberrypi')

    packet = gpsd.get_current()
    print(packet.position())
    xy_error,z_error =packet.position_precision()
    GPSlatidude,GPSlongitude =(packet.position())
    old_xtile = 0
    old_ytile = 0
    zoom=20
    maps=config.config('config.ini','Maps')
    mapmgr = Map(BaseURL=maps['baseurl'],token=maps['token'])

    lon = []
    lat = []
    try:
        with open('test_5m_grid_v2.csv', newline='') as csvfile:
            header= csvfile.readline()
            grid_reader= csv.reader(csvfile, delimiter=',')

            for row in grid_reader:
                #print(row)
                lat.append(float(row[2]))
                lon.append(float(row[1]))
    except:
        print('check csv file')
    plt.tight_layout()

    fig, ax = plt.subplots(figsize=(8, 7))
    # ax.scatter(lon,lat, zorder=1, alpha= 0.2, c='b', s=10)

    scale = 15

    while True:
        packet = gpsd.get_current()
        print(packet.position())
        xy_error, z_error = packet.position_precision()
        GPSlatidude, GPSlongitude = (packet.position())

        devicePos = Point(GPSlatidude, GPSlongitude)
        x_tile,y_tile= deg2num(devicePos.latitude, devicePos.longitude, zoom)

        (x, y) = deg2num(devicePos.latitude,devicePos.longitude, zoom)

        A = Point(geodesic(meters=scale).destination(devicePos, 0).format_decimal())
        B = Point(geodesic(meters=scale).destination(devicePos, 90).format_decimal())
        C = Point(geodesic(meters=scale).destination(devicePos, 180).format_decimal())
        D = Point(geodesic(meters=scale).destination(devicePos, 270).format_decimal())
        ax.cla()
        ax.set_axis_off()

        ax.set_xlim(min(A.longitude,B.longitude,C.longitude,D.longitude), max(A.longitude,B.longitude,C.longitude,D.longitude))
        ax.set_ylim(min(A.latitude,B.latitude,C.latitude,D.latitude), max(A.latitude,B.latitude,C.latitude,D.latitude))

        ax.plot(devicePos.longitude,devicePos.latitude, 'o', color='r')

        lon_error, lat_error =meter2deg(devicePos,xy_error)
        print(f"xy:+-{xy_error}m lon:+-{lon_error}°,lat:+-{lat_error}°")
        ax.add_artist(Ellipse((devicePos.longitude,devicePos.latitude), height=lat_error, width=lon_error, color='blue',fill=False))

        if not(old_xtile == x_tile) and not (old_ytile == y_tile):
            mapmgr.clear_tile_list()
            mapmgr.add_tile(x_tile, y_tile,zoom)
            mapmgr.add_tile(x_tile+1, y_tile, zoom)
            mapmgr.add_tile(x_tile, y_tile+1, zoom)
            mapmgr.add_tile(x_tile-1, y_tile, zoom)
            mapmgr.add_tile(x_tile , y_tile-1, zoom)
            old_xtile = x_tile
            old_ytile = y_tile
        plotTileList( mapmgr.get_tilSet())
        plt.pause(2)

    plt.show()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
