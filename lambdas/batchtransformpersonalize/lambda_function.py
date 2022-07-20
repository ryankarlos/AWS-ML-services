import os
import logging
import boto3
import pandas as pd
import numpy as np
import urllib.parse
import io
import json
import awswrangler as wr

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")

metadata_key = os.environ["METADATA_KEY"]


def lambda_handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    results_key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    results_obj = s3.get_object(Bucket=bucket, Key=results_key)
    metadata_obj = s3.get_object(Bucket=bucket, Key=metadata_key)
    df_metadata = pd.read_csv(
        io.BytesIO(metadata_obj["Body"].read()), index_col="movieId"
    )
    bytes_list = results_obj["Body"].read().rstrip(b"").split(b"\n")
    result = {"userId": [], "Recommendations": []}
    for data in bytes_list:
        if data != b"":
            results_dict = json.loads(data.decode("utf-8"))
            if results_dict["error"] is None:
                recommended_items = np.array(
                    results_dict["output"]["recommendedItems"], dtype=int
                )
                new_df = df_metadata.loc[recommended_items, :].reset_index(drop=True)
                recomendations = " | ".join(
                    list(
                        new_df["title"]
                        + " "
                        + "("
                        + new_df["genres"].str.split(pat="|", n=1).str[0]
                        + ")"
                    )
                )
                result["Recommendations"].append(recomendations)
                result["userId"].append(results_dict["input"]["userId"])

    transformed_batch = pd.DataFrame(result)
    print(transformed_batch)
    results_key = f'{results_key.rsplit("/", 1)[0]}/transformed_batch.csv'
    s3_output_path = f"s3://{bucket}/{results_key}"
    wr.s3.to_csv(df=transformed_batch,path=s3_output_path)
