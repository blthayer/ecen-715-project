"""Module to combine all NYISO data with the weather data."""
import pandas as pd
from combine_nyiso_data import LMP_DAY_AHEAD_FILE, LMP_REALTIME_FILE,\
    LOAD_FORECAST_FILE, LOAD_REALTIME_FILE
from clean_weather_data import OUT_FILE as WEATHER_FILE

OUTFILE = 'all_data.csv'


def print_consecutive_nans(df):
    # https://stackoverflow.com/questions/29007830/identifying-consecutive-nans-with-pandas
    for c in df.columns:
        n = df[c].isnull().astype(int).groupby(df[c].notnull().astype(
            int).cumsum()).sum().max()
        print('Max consecutive NaNs in {}: {:d}'.format(c, n))


def main():
    # Read files.
    lmp_forecast = pd.read_csv(LMP_DAY_AHEAD_FILE, header=[0, 1], index_col=0,
                               parse_dates=True, infer_datetime_format=True)
    print('lmp forecast data loaded.', flush=True)

    lmp_realtime = pd.read_csv(LMP_REALTIME_FILE, header=[0, 1], index_col=0,
                               parse_dates=True, infer_datetime_format=True)
    print('lmp realtime data loaded.', flush=True)

    load_forecast = pd.read_csv(LOAD_FORECAST_FILE, index_col=0,
                                parse_dates=True, infer_datetime_format=True)
    print('load forecast data loaded.', flush=True)

    load_realtime = pd.read_csv(LOAD_REALTIME_FILE, header=[0, 1],
                                index_col=0, parse_dates=True,
                                infer_datetime_format=True)
    print('load realtime data loaded.', flush=True)

    weather = pd.read_csv(WEATHER_FILE, index_col=0, parse_dates=True,
                          infer_datetime_format=True)
    print('weather data loaded.', flush=True)

    # Flatten multi-indexes.
    # https://stackoverflow.com/questions/14507794/pandas-how-to-flatten-a-hierarchical-index-in-columns
    lmp_forecast.columns = \
        ['_'.join(col).strip().replace(' ', '_') for col in
         lmp_forecast.columns.values]

    lmp_realtime.columns = ['_'.join(col).strip().replace(' ', '_') for col in
                            lmp_realtime.columns.values]

    load_realtime.columns = ['_'.join(col).strip().replace(' ', '_') for col in
                             load_realtime.columns.values]

    # Clean column names for pre-join.
    lmp_forecast.columns = \
        ['forecast_' + col.replace('($/MWHr)', '').lower() for
         col in lmp_forecast.columns.values]

    lmp_realtime.columns = \
        ['realtime_' + col.replace('($/MWHr)', '').lower() for
         col in lmp_realtime.columns.values]

    load_forecast.columns = \
        ['forecast_load_' + col.lower() for col in load_forecast.columns.values]

    load_realtime.columns = \
        ['realtime_' + col.lower() for col in load_realtime.columns.values]

    weather.columns = \
        [col.lower().replace('hourly', '') for col in weather.columns.values]

    print('Columns renamed.', flush=True)

    # Re-index all DataFrames. For whatever reason, they are not
    # DatetimeIndexes.
    for df in [lmp_forecast, lmp_realtime, load_forecast, load_realtime,
               weather]:
        df.index = pd.to_datetime(df.index, utc=True)
        df.sort_index()

    print('All indexes converted to DateTimeIndexes.', flush=True)

    # It turns out our realtime LMP and realtime load have some
    # missing values.
    # First, print the number of consecutive NaNs in each columns for
    # these two DataFrames.
    print('*' * 80)
    print('LMP Realtime')
    print_consecutive_nans(lmp_realtime)
    print('*' * 80)
    print('Load Realtime')
    print_consecutive_nans(load_realtime)

    # Fill via interpolation.
    lmp_realtime.interpolate(method='time', inplace=True)
    load_realtime.interpolate(method='time', inplace=True)

    # Our forecasts are hourly, but we want to re-index to 5 minutes.
    lmp_forecast = \
        lmp_forecast.resample('5min').asfreq().fillna(method='ffill')

    load_forecast = \
        load_forecast.resample('5min').asfreq().fillna(method='ffill')

    print('Hourly forecasts re-sampled.', flush=True)
    # Join data.
    all_data = lmp_forecast.join(other=[lmp_realtime, load_forecast,
                                        load_realtime, weather], how='left')

    # Only include 2016-2018
    all_data.sort_index()
    all_data.tz_convert('America/New_York')
    all_data = all_data['2016':'2018']
    all_data.to_csv(OUTFILE)

    pass


if __name__ == '__main__':
    main()