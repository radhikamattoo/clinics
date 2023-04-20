import os
import pandas
import json
import geocoder

result = geocoder.arcgis(location="Regency Run, San Antonio, Texas")
if result.ok:
    coordinates = result.latlng
else:
    print('oops')