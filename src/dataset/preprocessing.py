import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def preprocess_dataset(df):
    """
    Clean and normalize the cloud provider dataset.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw cloud provider dataset.

    Returns
    -------
    pandas.DataFrame
        Processed dataset.
    """

    # Fill missing numeric values with column mean
    numeric_cols = [
        "Cost",
        "Availability",
        "Reliability",
        "Security",
        "Scalability",
        "Response_Time",
        "Throughput",
        "Support_Quality"
    ]

    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    # Normalize QoS values
    scaler = MinMaxScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    return df