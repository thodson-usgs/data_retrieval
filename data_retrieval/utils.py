"""
Useful utilities for data munging.
"""
import pandas as pd
from pandas.core.indexes.multi import MultiIndex
from pandas.core.indexes.datetimes import DatetimeIndex

def to_str(listlike):
    """Translates list-like objects into strings.

    Return:
        List-like object as string
    """
    if type(listlike) == list:
        return ','.join(listlike)

    elif type(listlike) == pd.core.series.Series:
        return ','.join(listlike.tolist())

    elif type(listlike) == pd.core.indexes.base.Index:
        return ','.join(listlike.tolist())

    elif type(listlike) == str:
        return listlike

def mmerge_asof(left, right, tolerance=None, **kwargs):
    """Merges two dataframes with multi-index.

    Only works on two-level multi-index where the second level is a time.

    Parameters
    ----------
    left : DataFrame

    right : DataFrame

    tolerance : integer or Timedelta, optional, default None
        Select asof tolerance within this range; must be compatible with the merge index.

    Returns
    -------
    merged : DataFrame

    Examples
    --------
    TODO
    """
    # if not multiindex pass  to merge_asof
    if not isinstance(left.index, MultiIndex) and not isinstance(right.index, MultiIndex):
        return pd.merge_asof(left, right,
                             tolerance=tolerance,
                             right_index=True,
                             left_index=True)

    elif left.index.names != right.index.names:
        raise TypeError('Both indexes must have matching names')

    #check that lowest level is the datetime index

    #check that their are only two levels

    out_df = pd.DataFrame()
    dt_name = left.index.names[1]
    #TODO modify to handle more levels
    index_name = left.index.names[0]

    left_temp = left.reset_index().dropna(subset=[dt_name]).sort_values([dt_name])
    right_temp = right.reset_index().dropna(subset=[dt_name]).sort_values([dt_name])

    merged_df = pd.merge_asof(left_temp, right_temp,
                              tolerance=tolerance,
                              on=dt_name,
                              by=index_name)

    return merged_df.set_index([index_name, dt_name])
