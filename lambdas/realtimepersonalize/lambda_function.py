import os
import logging
import boto3
import pandas as pd
import json
import io

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")
iam = boto3.client("iam")
personalizeRt = boto3.client("personalize-runtime")

solution_arn = os.environ["SOLUTION_ARN"]
campaign_arn = os.environ["CAMPAIGN_ARN"]
num_results = os.environ["NUM_RESULTS"]
bucket = os.environ["BUCKET"]
metadata_key = os.environ["METADATA_KEY"]


def get_real_time_recommendations(
    campaign_arn, user_id, bucket, movies_key, num_results, **context
):
    if context:
        response = personalizeRt.get_recommendations(
            campaignArn=campaign_arn, userId=user_id, context=context
        )
    else:
        response = personalizeRt.get_recommendations(
            campaignArn=campaign_arn, userId=user_id, numResults=num_results
        )

    logger.info("Recommended items: \n")
    for item in response["itemList"]:
        movie_id = int(item["itemId"])
        title, genre = get_movie_names_from_id(bucket, movies_key, movie_id)
        print(f"{title} ({genre})")
    return response


def get_movie_names_from_id(bucket, key, movie_id):
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj["Body"].read()))
    title = df.loc[df["movieId"] == movie_id, ["title"]].values.flatten()[0]
    genre = df.loc[df["movieId"] == movie_id, ["genres"]].values.flatten()[0]
    return title, genre


def lambda_handler(event, context):
    user_id = event["user_id"]
    context_metadata = event.get("context", "{}")
    context_metadata = json.loads(context_metadata)
    if len(context_metadata) == 0:
        logger.info(
            f"Generating {num_results} recommendations for user {user_id} using campaign {campaign_arn}"
        )
    else:
        logger.info(
            f"Generating recommendations for user {user_id} using campaign {campaign_arn}, with provided context: \n\n {context_metadata}"
        )
    return get_real_time_recommendations(
        campaign_arn, user_id, bucket, metadata_key, num_results, **context_metadata
    )
