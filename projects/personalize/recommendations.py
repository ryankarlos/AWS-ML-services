import boto3
import click
import json
import logging
import sys
import pandas as pd
import io

personalize_rec = boto3.client(service_name="personalize")
personalizeRt = boto3.client("personalize-runtime")
s3 = boto3.client("s3")
iam = boto3.client("iam")

logger = logging.getLogger("recommendations")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


def create_batch_segment_job(
    input_s3_path, output_s3_path, job_name, num_users, role_arn, sol_ver_arn
):
    """
    create a batch segment job with the CreateBatchSegmentJob operation
    https://docs.aws.amazon.com/personalize/latest/dg/recommendations.html
    :param input_s3_path:Amazon S3 path to your input file
    :param output_s3_path: Amazon S3 path to your output location
    :param job_name:name of job
    :param num_users:number of users you want Amazon Personalize to predict for each line of input data
    :param role_arn:ARN of the IAM service role you created for Amazon Personalize during set up.
    :param sol_ver_arn: Amazon Resource Name (ARN) of your solution version
    :return:
    """
    response = personalize_rec.create_batch_segment_job(
        solutionVersionArn=sol_ver_arn,
        jobName=job_name,
        numResults=num_users,
        roleArn=role_arn,
        jobInput={"s3DataSource": {"path": input_s3_path}},
        jobOutput={"s3DataDestination": {"path": output_s3_path}},
    )
    logger.info(f"Response: \n\n {response}")
    return response


def create_batch_inference_job(
    input_s3_path, output_s3_path, job_name, role_arn, sol_ver_arn, num_results, config
):
    """
    Create a batch inference job to get batch item recommendations for users based on input data from Amazon S3.
    https://docs.aws.amazon.com/personalize/latest/dg/recommendations.html
    :param input_s3_path:Amazon S3 path to your input file
    :param output_s3_path:Amazon S3 path to your output location
    :param job_name:name of job
    :param role_arn:ARN of the IAM service role which has read and write access to input and output Amazon S3 buckets respectively.
    :param sol_ver_arn:Amazon Resource Name (ARN) of your solution version
    :param weight:User-Personalization recipe specific itemExplorationConfig hyperparameter, explorationWeight. Defaults to 0.3
    :param cutoff:User-Personalization recipe specific itemExplorationConfig hyperparameter, explorationcutoff. Defaults to 30
    :return:
    """
    config = json.loads(config)
    response = personalize_rec.create_batch_inference_job(
        solutionVersionArn=sol_ver_arn,
        jobName=job_name,
        roleArn=role_arn,
        numResults=num_results,
        batchInferenceJobConfig=config,
        jobInput={"s3DataSource": {"path": input_s3_path}},
        jobOutput={"s3DataDestination": {"path": output_s3_path}},
    )
    logger.info(f"Response: \n\n {response}")
    return response


def get_real_time_recommendations(
    campaign_arn, user_id, bucket, movies_key, num_results, **context
):
    """
    To get personalized recommendations or similar item recommendations from an Amazon Personalize campaign.
    If your campaign uses contextual metadata (for requirements see Increasing recommendation relevance with
    contextual metadata)
    optionally provide context data.For each context, for the Key, enter the metadata field, and for the Value, enter
    the context data.
    e.g. the key could be DEVICE and the value could be mobile phone.
    https://docs.aws.amazon.com/personalize/latest/dg/recommendations.html
    :param campaign_arn:Arn of campaign created
    :param user_id:user ID that is in the data that you used to train the solution
    :param num_results:number of recommended items. Defaults to 10
    :param context: To get a recommendation based on contextual metadata. provide the metadata field as the key and the
    context data as the value.
    :return:
    """

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


@click.command()
@click.option(
    "--bucket", default="recommendation-sample-data", help="bucket name",
)
@click.option(
    "--batch_input_key",
    default="movie-lens/batch/input/users.json",
    help="key for data for batch recommendations",
)
@click.option(
    "--batch_results_key",
    default="movie-lens/batch/results/",
    help="key for batch prediction results",
)
@click.option(
    "--movies_data_key",
    default="movie-lens/raw_data/input/movies.csv",
    help="key for raw movies dataset containing movie titles and id mapping",
)
@click.option(
    "--job_name", help="Name of job",
)
@click.option(
    "--sol_arn", help="arn of solution version to use",
)
@click.option(
    "--role_name", default="PersonalizeRole", help="role name which has access to S3",
)
@click.option(
    "--num_users",
    default=10,
    type=click.INT,
    help="number of users to predict for in each line of input data",
)
@click.option(
    "--config",
    default='{"itemExplorationConfig": {"explorationWeight": "0.3", "explorationItemAgeCutOff": "30"}}',
    help="User-Personalization recipe specific itemExplorationConfig hyperparameters: explorationWeight and explorationcutoff",
)
@click.option(
    "--campaign_arn", help="For realtime recommendation. Arn of campaign",
)
@click.option(
    "--user_id",
    help="For real time recommendation. user ID that is in the data that you used to train the solution",
)
@click.option(
    "--num_results",
    default=10,
    type=click.INT,
    help="number of recommended items for real time recommendation",
)
@click.option(
    "--context",
    default="{}",
    help="optional context metadata for real time prediction. If left as default, will run recommendations without "
    "context and num_results param needs to be passed.",
)
@click.option(
    "--recommendation_mode",
    default="batch_inference",
    type=click.Choice(["batch_inference", "batch_segment", "realtime"]),
    help="whether to generate batch or realtime predictions",
)
def main(
    recommendation_mode,
    bucket,
    batch_input_key,
    batch_results_key,
    movies_data_key,
    job_name,
    sol_arn,
    role_name,
    num_users,
    config,
    campaign_arn,
    user_id,
    num_results,
    context,
):
    s3_input_path = f"s3://{bucket}/{batch_input_key}"
    s3_inference_results_path = f"s3://{bucket}/{batch_results_key}/inference/"
    s3_segment_results_path = f"s3://{bucket}/{batch_results_key}/segment/"
    role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]
    if recommendation_mode == "batch_inference":
        logger.info(f"Running batch inference job {job_name} with config: {config}")
        return create_batch_inference_job(
            s3_input_path,
            s3_inference_results_path,
            job_name,
            role_arn,
            sol_arn,
            num_results,
            config,
        )
    elif recommendation_mode == "batch_segment":
        logger.info(f"Running batch segment job {job_name} for {num_users} users")
        return create_batch_segment_job(
            s3_input_path,
            s3_segment_results_path,
            job_name,
            num_users,
            role_arn,
            sol_arn,
        )
    elif recommendation_mode == "realtime":
        context = json.loads(context)
        if len(context) == 0:
            logger.info(
                f"Generating {num_results} recommendations for user {user_id} using campaign {campaign_arn}"
            )
        else:
            logger.info(
                f"Generating recommendations for user {user_id} using campaign {campaign_arn}, with provided context: \n\n {context}"
            )
        return get_real_time_recommendations(
            campaign_arn, user_id, bucket, movies_data_key, num_results, **context
        )
    else:
        raise ValueError(
            f"inference mode must be either 'batch_inference', 'batch_segment' or 'realtime'. You specified "
            f"{recommendation_mode}"
        )


if __name__ == "__main__":
    main()
