import pandas as pd


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
