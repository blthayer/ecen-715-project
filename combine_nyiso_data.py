"""Module to combine NYISO files into one file per type.

The module get_nyiso_data.py should be run first.
"""
# Imports from get_nyiso_data.py
from get_nyiso_data import LMP_DAY_AHEAD_ZONAL, LMP_REALTIME_ZONAL,\
    LOAD_FORECAST, LOAD_REALTIME, START_YEAR, END_YEAR, START_MONTH, \
    END_MONTH, get_date_str

# Third-party:
import pandas as pd

# Standard library:
import os
from copy import deepcopy

# Constants:
LMP_DAY_AHEAD_FILE = 'lmp_day_ahead.csv'


def get_file_list(root_dir):
    """Helper to get listing of files for a root directory (root_dir).

    This function operates on the assumption that data was generated via
    get_nyiso_data.py. A more general method would recurse.
    """
    # Initialize list.
    all_files = []

    # Loop over the years and months.
    for year in range(START_YEAR, END_YEAR+1):
        for month in range(START_MONTH, END_MONTH+1):
            # Get a date string.
            date_str = get_date_str(year=year, month=month)

            # Construct string for this directory.
            this_dir = os.path.join(root_dir, date_str)

            # Get listing of files and sort them to save sorting later.
            files = os.listdir(this_dir)
            files.sort()

            # Extend the list of all files.
            all_files.extend([os.path.join(root_dir, date_str, f)
                              for f in files])

    return all_files


def read_all_files(files):
    """Helper to read all files in list into a DataFrame."""
    return pd.concat([pd.read_csv(f, index_col=0, parse_dates=True,
                                  infer_datetime_format=True) for f in files])


def clean_columns(df):
    """Helper to do some standard cleaning on DataFrame columns.

    1) Make 'Name' categorical
    2) Remove spaces and periods from 'Name'
    3) Drop PTID (we have name, why use the ID?)
    """
    # Drop col1. Also drop PTID while we're at it, as we don't need it.
    df.drop(axis=1, labels=['PTID'], inplace=True)

    # Make 'Name' categorical
    df['Name'] = df['Name'].astype('category')

    # Remove spaces and periods from the names:
    df['Name'] = \
        df['Name'].apply(lambda x: x.replace(' ', '').replace('.', ''))

    return df


def localize_times(df):
    """Helper to get the times from naive to aware, as we have to deal
    with daylight savings.
    """
    # Well, we're in a pickle. We need to pivot the DataFrame. However,
    # we can't pivot until we've removed duplicates. Why do we have
    # duplicates? Daylight savings time. What's the fix? tz_localize.
    # However, tz_localize fails because it detects multiple transitions
    # (because we haven't pivoted, there are date duplicates!). See the
    # paradox?
    #
    # So far, our data isn't terribly large in memory. So, let's loop
    # over the different are names, create copies of the DataFrames,
    # localize the time, then create a new DataFrame which we can pivot.

    df_list = []
    # Group by 'Name', loop over the groups, and localize the
    # sub-indices
    groups = df.groupby('Name')
    for g in groups:
        # Extract the group for this area.
        sub_df = groups.get_group(g[0])

        # Make a deep copy.
        new_df = deepcopy(sub_df)

        # Localize the time index.
        new_df.index = new_df.index.tz_localize('America/New_York',
                                                ambiguous='infer')
        # Put the new localized df in our list.
        df_list.append(new_df)

    # Overwrite our 'df' variable.
    df = pd.concat(df_list)

    return df


def combine_lmp_day_ahead():
    """Combine day ahead LMP files into one."""
    # Get all day-ahead LMP files.
    files = get_file_list(root_dir=LMP_DAY_AHEAD_ZONAL)

    # Read 'em all.
    df = read_all_files(files)

    # Some files have a 'Marginal Cost Congestion ($/MWH' column instead
    # of a 'Marginal Cost Congestion ($/MWHr)' column.
    # Ensure the number of NaN's in both columns sum to be the length
    # of the data:
    col1 = 'Marginal Cost Congestion ($/MWH'
    col2 = 'Marginal Cost Congestion ($/MWHr)'
    col1_na = df[col1].isnull().sum()
    col2_na = df[col2].isnull().sum()
    assert col1_na + col2_na == df.shape[0]

    # Zero out NaN's in those columns.
    df.fillna(value={col1: 0, col2: 0}, inplace=True)

    # Add col1 and col2
    df[col2] = df[col1] + df[col2]

    # Drop col1. Also drop PTID while we're at it, as we don't need it.
    df.drop(axis=1, labels=[col1], inplace=True)

    # Clean up columns.
    df = clean_columns(df)

    # Localize the times. This is time consuming (heh).
    df = localize_times(df)

    # Pivot.
    df_pivot = df.pivot(columns='Name')

    df_pivot.to_csv(LMP_DAY_AHEAD_FILE)


def main():
    combine_lmp_day_ahead()
    pass


if __name__ == '__main__':
    main()
