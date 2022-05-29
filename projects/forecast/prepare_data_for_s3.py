from common import s3_client
import dask.dataframe as dd
import dask
from pathlib import Path
import re


def read_raw_csv(path):
    p = Path(path)
    for x in p.iterdir():
        if x.suffix == ".csv":
            m = re.search(r"(?<=_)\w+", x.name)
            assert m.group(0) == "manning"
            basepath = str(x)
    print(f"Reading data from {basepath}")
    df = dd.read_csv(basepath)
    return df, basepath


@dask.delayed
def parse_dt_to_year(df):
    df["year"] = dd.to_datetime(df["ds"], format="%Y-%m-%d").dt.year
    return df


@dask.delayed
def filter_df_by_year(df, year=2015):
    df_cleaned = df.loc[df["year"] >= year, ["ds", "y"]].reset_index(drop=True)
    return df_cleaned


@dask.delayed
def reformat_for_aws_forecast(df):
    df_renamed = df.rename(columns={"ds": "timestamp", "y": "target_value"})
    df_renamed["item_id"] = "1"
    return df_renamed


def save_data_for_s3(df, basepath, filename):
    filepath = Path(basepath).parents[0].joinpath("data", filename)
    print(filepath)
    p = filepath.parents[0]
    destination_path = str(filepath)
    p.mkdir(parents=True, exist_ok=True)
    df.to_csv(destination_path, index=False)
    return destination_path


def create_bucket(bucket_name):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    # Create bucket
    try:
        response = s3_client.create_bucket(Bucket=bucket_name)
        print(response)
    except s3_client.BucketAlreadyExists as e:
        print(f"bucket {bucket_name} already exists")


def put_object_in_s3_bucket(bucket_name, filepath):
    create_bucket(s3_client, bucket_name)
    filename = Path(filepath).name
    s3_client.upload_file(filepath, bucket_name, filename)
