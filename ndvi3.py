 # wget https://s3-us-west-2.amazonaws.com/landsat-pds/c1/L8/111/082/LC08_L1TP_111082_20170519_20170519_01_RT/LC08_L1TP_111082_20170519_20170519_01_RT_B4.TIF -O RED_2010519.TIF
 # wget https://s3-us-west-2.amazonaws.com/landsat-pds/c1/L8/111/082/LC08_L1TP_111082_20170519_20170519_01_RT/LC08_L1TP_111082_20170519_20170519_01_RT_B5.TIF -O NIR_2010519.TIF

 # gdal_translate -a_nodata 0 RED_2010519.TIF -ot Float32 -of GTiff RED1.TIF
 # gdal_translate -a_nodata 0 NIR_2010519.TIF -ot Float32 -of GTiff NIR1.TIF
 # python ndvi3.py RED1.TIF NIR1.TIF AAA_NDVI.TIF


# NDVI Python Script
#
# GNU GENERAL PUBLIC LICENSE
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# Created by Alexandros Falagas.
#
from osgeo import gdal
from sys import argv
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()
from gdalconst import *
import numpy as np
import sys
import os
import errno

t = np.float32;

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def contrast_stretch(im, NoDataValue=None):
  """
  Performs a simple contrast stretch of the given image, from 5-95%.
  """
  # in_min = np.percentile(im, 2)
  # in_max = np.percentile(im, 98)

  # out_min = 0.0
  # out_max = 255.0
  # out = im

  out = np.add(np.multiply(im, 128.0),128.0)

  out = out.astype(np.ubyte)

  return out

def downloadFiles(product):
# LC08_L1TP_111084_20170519_20170525_01_T1  
  downloadDir = "/code/tmp/"+product
  make_sure_path_exists(downloadDir);

  if (product.find("_") > -1):
    path = product[10:13]
    row = product[13:16]
    url="https://landsat-pds.s3.amazonaws.com/c1/L8/"+path+"/"+row+"/"+product+"/"+product
    url="https://landsat-pds.s3.amazonaws.com/c1/L8/"+path+"/"+row+"/"+product+"/"+product
  else:
    path = product[11:13]
    row = product[14:16]
#    https://landsat-pds.s3.amazonaws.com/L8/139/045/LC81390452014295LGN00/index.html
    url="https://landsat-pds.s3.amazonaws.com/L8/"+path+"/"+row+"/"+product+"/"+product
    
  print "BaSEURL = "+url

  print " Going to download :"+url+"_B4.TIF"
  print " Going to download :"+url+"_B5.TIF"

  #os.system("wget "+url+"_B4.TIF -O "+downloadDir+"/B4.TIF")
  os.system("gdal_translate -a_srs EPSG:4326 -a_nodata 0 -of GTiff -ot Float32 "+downloadDir+"/B4.TIF "+downloadDir+"/B4_NODATA.TIF")
  #os.system("wget "+url+"_B5.TIF -O "+downloadDir+"/B5.TIF")
  os.system("gdal_translate -a_srs EPSG:4326 -a_nodata 0 -of GTiff -ot Float32 "+downloadDir+"/B5.TIF "+downloadDir+"/B5_NODATA.TIF")

def calculateNDVI(product):
  # red, nir = map(gdal.Open, argv[1:3])
  red = gdal.Open("/code/tmp/"+product+"/B4_NODATA.TIF", GA_ReadOnly);
  nir = gdal.Open("/code/tmp/"+product+"/B5_NODATA.TIF", GA_ReadOnly);

  if red is None:
    print 'Could not open file'
    sys.exit(1)

  if nir is None:
    print 'Could not open file'
    sys.exit(1)

  r = np.array(red.GetRasterBand(1).ReadAsArray(0,0,red.RasterXSize,red.RasterYSize),dtype=float)
  n = np.array(nir.GetRasterBand(1).ReadAsArray(0,0,nir.RasterXSize,nir.RasterYSize),dtype=float)

  np.seterr(divide='ignore', invalid='ignore') #Ignore the divided by zero or Nan appears

  # Here's the meat of this whole thing, the actual NDVI formula:
  check = np.logical_and( r >= 1, n >= 1)
  ndvi = np.where(check, (n - r) / (n + r), -999)

  red=None
  nir=None

  return ndvi

def saveRaster(data, baseFile, outFile, format=None, NoDataValue=None):
  oformat = gdal.GDT_Float32

  if (format != None):
    oformat = format

  if (NoDataValue == None):
    NoDataValue = 0  

  # print "oformat=" + oformat
    
  res = gdal.Open(baseFile, GA_ReadOnly);
  geotr=res.GetGeoTransform()
  proj=res.GetProjection()
  sizeX=res.RasterXSize
  sizeY=res.RasterYSize

  res=None

  driver=gdal.GetDriverByName('GTiff')
  dst_ds=driver.Create(outFile, sizeX, sizeY, 1, oformat)
  dst_ds.SetGeoTransform(geotr)
  dst_ds.SetProjection(proj)
  dst_ds.GetRasterBand(1).SetNoDataValue(NoDataValue)
  dst_ds.GetRasterBand(1).WriteArray(data)

  min = dst_ds.GetRasterBand(1).GetMinimum()
  max = dst_ds.GetRasterBand(1).GetMaximum()

  if min is None or max is None:
    (min,max) = dst_ds.GetRasterBand(1).ComputeRasterMinMax(1)

  print "Max =" + str(max)
  print "Min =" + str(min)

  dst_ds=None # save, close

      

if __name__ == "__main__":
  product = argv[1]

  downloadFiles(product)

  c_ndvi = calculateNDVI(product)

  infile = "/code/tmp/"+product+"/B4.TIF"
  outfile = "/code/tmp/"+product+"/temp_ndvi.tif"
  finalDir = "./output/ndvi/"+product
  make_sure_path_exists(finalDir);
  saveRaster(c_ndvi, infile, outfile, gdal.GDT_Float32,-999)

  ndvi = contrast_stretch(c_ndvi, -999)

  outfile1 = "/code/tmp/"+product+"/temp_ndvi1.tif"
  saveRaster(ndvi, infile, finalDir+"/ndvi.tif", gdal.GDT_Byte, 0)


  # os.system("gdalwarp -t_srs epsg:4326 /code/tmp/"+product+"/temp_ndvi1.tif "+finalDir+"/ndvi.tif")
  #os.system("gdal_translate -a_nodata 127 -of GTiff temp01.tif "+argv[3])
  #os.system("gdal_translate -a_nodata 127 -of GTiff temp01.tif temp03.tif")
  # os.system("gdal_translate -scale 0 255 "+str(ndvi.min())+" "+str(ndvi.max())+" -a_nodata 0 -of GTiff -ot Byte /code/tmp/"+product+"/temp_ndvi1.tif "+finalDir+"/ndvi.tif")

  print 'The NDVI image is saved as : ',finalDir+"/ndvi.tif"

  #gdal_translate -a_srs EPSG:4326 -co COMPRESS=DEFLATE -co PREDICTOR=2 -co ZLEVEL=9
  #-a_nodata 0 -of GTiff 4B_NDVI.TIF 4C_NDVI.tif


  # http://localhost:8080/geoserver/gwc/rest/seed/AgSpace:Rainfall_previous_week
