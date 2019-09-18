"""Module to download NYISO LMP data.

Please read the NOTES section of nyiso_url.

Adapt the "main" section of the code to download what you would like.
"""
# Third-party:
import requests

# Built-in:
import os
from zipfile import ZipFile
from io import BytesIO

# Directories for saving data. Use these in the 'main' section.
LMP_DAY_AHEAD_ZONAL = 'nyiso_lmp_day_ahead_zonal'
LMP_REALTIME_ZONAL = 'nyiso_lmp_realtime_zonal'
LOAD_FORECAST = 'nyiso_load_forecast'
LOAD_REALTIME = 'nyiso_load_realtime'

# Years to grab data for (inclusive).
START_YEAR = 2009
END_YEAR = 2016
START_MONTH = 1
END_MONTH = 12

# Download URLs for NYISO. NOTE: You should only have one base, med, and
# end URL uncommented at a time.
NYISO_BASE_URL = 'http://mis.nyiso.com/public/csv/'


def get_date_str(year, month):
    """Simple helper for creating the NYISO date strings."""
    return str(year) + '{:02d}'.format(month) + '01'


def nyiso_url(data_type, day_ahead, date_str, zonal=True):
    """Helper function to formulate a URL for downloading NYISO data.

    :param data_type: String. Either 'load' or 'lmp.'
    :param day_ahead: Boolean. True for day ahead, False for real time.
    :param date_str: String. Represents date like YYYYMMDD.
    :param zonal: Boolean. True for zonal, False for generator.

    NOTES:
        - The zonal input is not used if data_type is 'load.'
        - For load forecast, URLs here are for the "NY Load Forecast"
            field, not the "Zonal Load Commitment" field. This can be
            updated if desired.
        - For actual load, URLs here are for the "Real-Time" field, not
            the "Integrated Real-Time" field. This can be updated if
            desired.
    """
    # Determine the middle and endings parts of the URL
    if data_type == 'lmp' and day_ahead:
        url_mid = 'damlbmp'

        # Examples:
        # http://mis.nyiso.com/public/csv/damlbmp/20181101damlbmp_zone_csv.zip
        # http://mis.nyiso.com/public/csv/damlbmp/20181201damlbmp_gen_csv.zip

    elif data_type == 'lmp' and not day_ahead:
        url_mid = 'realtime'
        # http://mis.nyiso.com/public/csv/realtime/20181001realtime_zone_csv.zip
        # http://mis.nyiso.com/public/csv/realtime/20181101realtime_gen_csv.zip
        # Examples:

    elif data_type == 'load' and day_ahead:
        url_mid = 'isolf'
        # Example:
        # http://mis.nyiso.com/public/csv/isolf/20180101isolf_csv.zip

    elif data_type == 'load' and not day_ahead:
        url_mid = 'pal'
        # Example:
        # http://mis.nyiso.com/public/csv/pal/20180501pal_csv.zip
    else:
        raise ValueError("data_type must be 'load' or 'lmp' and day_ahead "
                         "must be a boolean.")

    # Determine the end part of the URL
    if data_type == 'lmp':
        if zonal:
            url_end = '_zone'
        else:
            url_end = '_gen'
    if data_type == 'load':
        url_end = ''

    # Construct the full URL.
    # noinspection PyUnboundLocalVariable
    url = '{base}/{mid}/{date}{mid}{e}_csv.zip'.format(base=NYISO_BASE_URL,
                                                       mid=url_mid,
                                                       date=date_str,
                                                       e=url_end)

    return url


def get_data(data_dir, data_type, day_ahead, zonal, start_year=2016,
             end_year=2018, start_month=1, end_month=12):
    """Helper function for downloading NYISO data.

    It's worth reading the "notes" section of the docstring for the
    nyiso_url function.

    :param data_dir: String. Directory to save data,
    :param data_type: String. Either 'load' or 'lmp.'
    :param day_ahead: Boolean. True for day ahead, False for real time.
    :param zonal: Boolean. True for zonal, False for generator.
    :param start_year: Integer. Starting year to pull data.
    :param end_year: Integer. Ending year to pull data.
    :param start_month: Integer. Starting month to pull data.
    :param end_month: Integer. Ending month to pull data.
    """
    # Create directory for NYISO LMP data
    try:
        os.mkdir(data_dir)
    except OSError:
        # If the directory already exists, don't complain.
        pass

    # NYISO stores data in monthly archives. Loop.
    for year in range(start_year, end_year+1):
        # Loop over months.
        for month in range(start_month, end_month+1):
            # Create a string for the date.
            date_str = get_date_str(year, month)
            print('Downloading data for {}...'.format(date_str), end='',
                  flush=True)

            # Formulate the URL.
            url = nyiso_url(data_type=data_type, day_ahead=day_ahead,
                            zonal=zonal, date_str=date_str)

            # Download the data.
            r = requests.get(url)

            if not r.ok:
                raise UserWarning('Failed to download for {}'.format(date_str))

            # Get data into ZIP archive.
            z = ZipFile(BytesIO(r.content))

            # Create directory for this archive.
            this_dir = os.path.join(data_dir, date_str)
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


if __name__ == '__main__':
    # Download all the zonal data.
    # print('Downloading day ahead zonal LMP data.')
    # get_data(data_dir=LMP_DAY_AHEAD_ZONAL, data_type='lmp',
    #          day_ahead=True, zonal=True, start_year=START_YEAR,
    #          end_year=END_YEAR, start_month=START_MONTH, end_month=END_MONTH)
    # print('*' * 80)
    #
    # print('Downloading realtime zonal LMP data.')
    # get_data(data_dir=LMP_REALTIME_ZONAL, data_type='lmp',
    #          day_ahead=False, zonal=True, start_year=START_YEAR,
    #          end_year=END_YEAR, start_month=START_MONTH, end_month=END_MONTH)
    # print('*' * 80)
    #
    # print('Downloading forecast load data.')
    # get_data(data_dir=LOAD_FORECAST, data_type='load',
    #          day_ahead=True, zonal=True, start_year=START_YEAR,
    #          end_year=END_YEAR, start_month=START_MONTH, end_month=END_MONTH)
    # print('*' * 80)

    print('Downloading realtime load data.')
    get_data(data_dir=LOAD_REALTIME, data_type='load',
             day_ahead=False, zonal=True, start_year=START_YEAR,
             end_year=END_YEAR, start_month=START_MONTH, end_month=END_MONTH)
