"""Module to clean up the weather data.

First, download the "Weather Data" folder from
https://drive.google.com/open?id=1PyXQ1l-J2OHQd5P5tts8QCoLZC7R9e6w

Then, extract the archive here and name it rename the directory
"Weather_Data"
"""
import pandas as pd
import os

# Extracting the archive led to nesting.
WEATHER_DIR = os.path.join("Weather_Data", "Weather Data")

# Hard-code the zones. Note there's no 'H'
ZONES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'I', 'J', 'K']

# Select the columns we want to pull from the weather files.
# NOTE: Make sure DATE is always first.
COLUMNS = ['DATE', 'HourlyDryBulbTemperature', 'HourlyRelativeHumidity',
           'HourlyWindSpeed']

# NOTE: using EST as it doesn't do daylight savings, which is true for
# this data.
TIMEZONE = 'EST'

# Output file.
OUT_FILE = 'all_weather.csv'

# For simplicity, drop features with more than 15 consecutive NaNs.
# TODO: Rather than dropping we should consider copying in the previous
#   day or something.
NAN_THRESHOLD = 15


def main():
    # Read all the data.
    dfs = [pd.read_csv(os.path.join(WEATHER_DIR, 'Zone{}.csv'.format(z)),
                       index_col=0, parse_dates=True, usecols=COLUMNS,
                       infer_datetime_format=True, low_memory=False)
           for z in ZONES]

    # Rename columns, force data to be numeric, localize time, and
    # drop duplicates.
    for idx, df in enumerate(dfs):
        # Grab zone information based on the index.
        zone = ZONES[idx]

        # Cast to numeric.
        # 'coerce' will return NaN for values which can't be cast.
        for c in COLUMNS[1:]:
            df[c] = pd.to_numeric(df[c], errors='coerce')

        # Rename columns.
        df.rename(lambda x: x + '_' + zone, axis='columns',
                  inplace=True)

        # Localize time.
        df.index = df.index.tz_localize(TIMEZONE, ambiguous='raise')

        # Drop duplicates.
        # TODO: should probably make a more educated decision about what
        #   to drop.
        dup_ind = df.index.duplicated(keep='first')
        df.drop(labels=df.index[dup_ind], axis=0, inplace=True)

        # Display NaN information:
        print('*' * 80)
        print('Zone {} NaN information:'.format(zone))
        print(df.isna().sum())

        # Display consecutive NaNs.
        # https://stackoverflow.com/questions/29007830/identifying-consecutive-nans-with-pandas
        for c in df.columns:
            n = df[c].isnull().astype(int).groupby(df[c].notnull().astype(
                int).cumsum()).sum().max()
            print('Max consecutive NaNs in {}: {:d}'.format(c, n))

            # If we've exceeded the NaN threshold, drop the feature.
            # TODO: we should use a more sophisticated method here, like
            #   filling spots with data from the previous day.
            if n > NAN_THRESHOLD:
                print('DROPPING {}.'.format(c))
                df.drop(labels=c, axis=1, inplace=True)

    # Join our DataFrames into one.
    # TODO: I think outer join is the most appropriate here?
    all_weather = dfs[0].join(other=dfs[1:], how='outer', sort=True)

    # Drop duplicates that stem from the outer join.
    # all_weather.drop_duplicates(keep='first', inplace=True)

    # Resample.
    all_weather = all_weather.resample('5min').asfreq()

    # Fill nan's by interpolating.
    # TODO: should we impose a limit via the 'limit' input?
    all_weather.interpolate(method='time', inplace=True)

    # Back fill the rest of the NaNs.
    all_weather.fillna(method='backfill', inplace=True)

    # Save to file.
    all_weather.to_csv(OUT_FILE)


if __name__ == '__main__':
    main()
