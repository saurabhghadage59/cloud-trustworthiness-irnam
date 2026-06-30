import pandas as pd


def load_dataset(path="src/dataset/cloud_dataset.csv"):
    """
    Load the cloud provider dataset.

    Args:
        path (str): Path to the CSV file.

    Returns:
        pandas.DataFrame: Loaded dataset.
    """
    return pd.read_csv(path)