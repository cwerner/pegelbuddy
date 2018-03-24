import sys
import textract
import datetime
import pandas as pd
import os


# convert image from GIF first, gis are bad
print('preparing image ...')
infile = sys.argv[1]
outfile = infile.replace('.GIF','.TIF')

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

df.to_csv('pegel.csv', index=False, sep=';')
