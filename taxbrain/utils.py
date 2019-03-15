"""
Helper functions for the various taxbrain modules
"""


def weighted_sum(df, var, wt="s006"):
    """
    Return the weighted sum of specified variable
    """
    return (df[var] * df[wt]).sum()
