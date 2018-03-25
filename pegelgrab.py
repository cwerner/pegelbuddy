import sys
import textract
import datetime
import pandas as pd
import os
import requests
import urllib.request

from collections import OrderedDict

import re
from bs4 import BeautifulSoup
import json
import requests
url = 'http://www.hvz.baden-wuerttemberg.de/map_peg.html'
page = requests.get(url).content
soup = BeautifulSoup(page, "html.parser")

data = soup.find_all("script")[4].string  #[19].string

# fix
z = data.split('var SiteStations = ')[1].split('//')[0].replace(';','')

import ast
mylist = ast.literal_eval(z)

cols = OrderedDict([('V%02d'%i, []) for i in range(23)])
df_stations = pd.DataFrame(cols)
for row in mylist:

    d_dict = dict([('V%02d'%i,v) for i, v in enumerate(row)])
    df_stations = df_stations.append(d_dict, ignore_index=True)

df_stations.to_csv('stations.csv', index=False, sep=";")


#
# http://www.hvz.baden-wuerttemberg.de/map_peg.html
#

# Download the file from `url` and save it locally under `file_name`:

for cnt, row in enumerate(df_stations.iterrows()):

    V17=row[1].loc['V17']
    
    fname=f"{V17}_LIS.GIF"
    
    #00163-140_LIS.GIF
    URL=f"http://www.hvz.baden-wuerttemberg.de/gifs/{fname}"
    urllib.request.urlretrieve(URL, os.path.join('gifs', fname))
    

    # convert image from GIF first, gis are bad
    print('preparing image ...')
    infile =  os.path.join('gifs', fname)
    outfile = infile.replace('.GIF','.TIF')
    outfile = os.path.basename(outfile)
    #cmd = f"convert {infile} -channel rgb -auto-level {outfile}"
    cmd = f"convert {infile} {outfile}"

    os.system(cmd)

    # this requires tesseract c++ library + python module as a backend

    print('ocr ...')
    text = textract.process(
        outfile,
        method='tesseract',
        language='eng',
        psm=5
    )


    print('cleanup and dump ...')

    x = text.decode('unicode_escape').replace(':','').replace('.','').replace(' ','') 
    x = x.split('\n')
    x = [i for i in x if len(i) == 17]
    x = [i for i in x if i[0] in '0123456789']

    df = pd.DataFrame()

    # error check assumes that first two lines are ok
    last2_date  = None
    last_date = None

    # check for year first

    for r in x:
        value = float(r[-3:-1]) + 0.1 * float(r[-1])
        date = datetime.datetime.strptime(r[:-3], '%d%m%Y%H%M%S')
        
        if date.year != 2018:
            date = date.replace(year=2018)

        if last_date:
            if last_date - datetime.timedelta(seconds=15*60) != date:
                if last2_date:
                    if last2_date - datetime.timedelta(seconds=30*60) != date:
                        # mismatch with two prvious times, correct:
                        new_date = last_date - datetime.timedelta(seconds=15*60)
                        print('ocr error; correct date', date, '->', new_date)
                        date = new_date

        if last_date:
            last2_date = last_date
        last_date = date
           
        df = df.append({'date': date, 'value': value}, ignore_index=True)

    outfile = os.path.basename(outfile)
    df.to_csv(os.path.join('csvs', outfile[:-4]+'.csv'), index=False, sep=';')

    if cnt == 150:
        exit()
