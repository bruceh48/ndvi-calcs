#!/bin/bash

OZ_OUTLINE="./australia-coastline/Australia.shp"

temp_dir=`mktemp -d`
rain_dir=`mktemp -d`

wget "http://www.bom.gov.au/web03/ncc/www/awap/rainfall/totals/week/grid/0.05/latest.grid.Z" -O "$rain_dir"/previous_week.grid.Z
gzip -d "$rain_dir"/previous_week.grid.Z

wget "http://www.bom.gov.au/web03/ncc/www/awap/rainfall/totals/daily/grid/0.05/latest.grid.Z" -O "$rain_dir"/previous_day.grid.Z
gzip -d "$rain_dir"/previous_day.grid.Z

wget "http://www.bom.gov.au/web03/ncc/www/awap/rainfall/totals/month/grid/0.05/latest.grid.Z" -O "$rain_dir"/previous_month.grid.Z
gzip -d "$rain_dir"/previous_month.grid.Z

wget "http://www.bom.gov.au/web03/ncc/www/awap/temperature/maxave/daily/grid/0.05/latest.grid.Z" -O "$temp_dir"/max_previous_day.grid.Z
gzip -d "$temp_dir"/max_previous_day.grid.Z

wget "http://www.bom.gov.au/web03/ncc/www/awap/temperature/minave/daily/grid/0.05/latest.grid.Z" -O "$temp_dir"/min_previous_day.grid.Z
gzip -d "$temp_dir"/min_previous_day.grid.Z


function makeGeoTif {
  GRIDFILE=$1
  OUTFILE=$2
  NODATA=${3:--999}

  DIR=$(dirname "${OUTFILE}")
  TDIR="/tmp"

  echo $GRIDFILE
  echo $OUTFILE
  echo $DIR

  TDIR=$(mktemp -d)

  if [ -f "$GRIDFILE" ]; then
    gdal_translate -a_srs EPSG:4326 $GRIDFILE $TDIR/tmp_01.tif
    if [ -f "$TDIR/tmp_01.tif" ]; then
      gdal_calc.py -A $TDIR/tmp_01.tif --NoDataValue=$NODATA --overwrite --outfile=$TDIR/tmp_02.tif --calc="A*(A>0.9)"
      gdal_calc.py -A $TDIR/tmp_02.tif --NoDataValue=$NODATA --overwrite --outfile=$TDIR/tmp_03.tif --type Float32 --calc="numpy.round(A,2)"

      mkdir -p $DIR
      rm -rf $OUTFILE
      gdalwarp -dstnodata $NODATA -q -cutline $OZ_OUTLINE -tr 0.05 0.05 -of GTiff $TDIR/tmp_03.tif $OUTFILE
    fi
  else
    echo "Cannot find raw grid file : $GRID"
  fi
  rm -r "$TDIR"
}

rm -rf ./output
mkdir -p ./output

makeGeoTif "$rain_dir"/previous_week.grid ./output/rain/previous_week/RAIN_previous_week.tif 0
makeGeoTif "$rain_dir"/previous_day.grid ./output/rain/previous_day/RAIN_previous_day.tif 0
makeGeoTif "$rain_dir"/previous_month.grid ./output/rain/previous_month/RAIN_previous_month.tif 0

makeGeoTif "$temp_dir"/min_previous_day.grid ./output/temp/min/TEMP_MIN_previous_day.tif -999
makeGeoTif "$temp_dir"/max_previous_day.grid ./output/temp/max/TEMP_MAX_previous_day.tif -999

rm -rf "$temp_dir"
rm -rf "$rain_dir"

echo "rsync -a ./output/rain ubuntu@dev-geoserver.agworld.co:/opt/data"
echo "rsync -a ./output/temp ubuntu@dev-geoserver.agworld.co:/opt/data"
