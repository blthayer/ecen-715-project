"""Module to download NYISO LMP data."""
# Third-party:
import requests

# Built-in:
import os
from zipfile import ZipFile
from io import BytesIO

# Data directory
DATA_DIR = 'nyiso_lmp'

# Download URLs for NYISO. NOTE: You should only have one base, med, and
# end URL uncommented at a time.
nyiso_base_url = 'http://mis.nyiso.com/public/csv/'
# Day ahead:
nyiso_med_url = 'damlbmp/'
# Real time:
# nyiso_med_url += 'realtime/'

# Day-ahead, by generator:
# nyiso_end_url = 'damlbmp_gen_csv.zip'
# Day-ahead, by zone:
nyiso_end_url = 'damlbmp_zone_csv.zip'
# Realtime, by zone:
# nyiso_end_url = 'realtime_zone_csv.zip'
# Realtime, by generator:
# nyiso_end_url = 'realtime_gen_csv.zip'

# Create directory for NYISO LMP data
try:
    os.mkdir(DATA_DIR)
except OSError:
    # If the directory already exists, don't complain.
    pass

# Define years of data to pull
start_year = 2016
end_year = 2018

# NYISO stores data in monthly archives. Loop.
for year in range(start_year, end_year+1):
    # Loop over months.
    for month in range(1, 13):
        # Create a string for the date.
        date_str = str(year) + '{:02d}'.format(month) + '01'
        print('Downloading data for {}...'.format(date_str), end='',
              flush=True)

        # Formulate the URL.
        url = nyiso_base_url + nyiso_med_url + date_str + nyiso_end_url

        # Download the data.
        r = requests.get(url)

        if not r.ok:
            raise UserWarning('Failed to download for {}'.format(date_str))

        # Get data into ZIP archive.
        z = ZipFile(BytesIO(r.content))

        # Create directory for this archive.
        this_dir = os.path.join(DATA_DIR, date_str)
        try:
            os.mkdir(this_dir)
        except OSError:
            # Don't complain if the directory already exists.
            pass

        # Extract data to directory.
        z.extractall(path=this_dir)

        # Print a dot for each file we've downloaded.
        print('done.', flush=True)
        pass
