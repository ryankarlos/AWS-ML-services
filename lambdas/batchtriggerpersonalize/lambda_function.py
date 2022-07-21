import os
import logging
import boto3
import json
import urllib.parse
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iam = boto3.client("iam")
personalize_rec = boto3.client(service_name="personalize")
s3 = boto3.client("s3")

timestamp_id = int(time.time())

solution_arn = os.environ["SOLUTION_ARN"]
results_key = os.environ["BATCH_RESULTS_KEY"]
job_name = f'{os.environ["JOB_NAME"]}_{timestamp_id}'
num_results = int(os.environ["NUM_RESULTS"])
role_name = os.environ["ROLE_NAME"]
config = os.environ["CONFIG"]
num_users = int(os.environ["NUM_USERS"])


def create_batch_segment_job(
    input_s3_path, output_s3_path, job_name, num_users, role_arn, sol_ver_arn
):
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


def lambda_handler(event, context):
    role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    s3_input_path = f"s3://{bucket}/{key}"
    s3_inference_results_path = f"s3://{bucket}/{results_key}/inference/"
    s3_segment_results_path = f"s3://{bucket}/{results_key}/segment/"
    try:
        if key.split("/")[-1] == "users.json":
            logger.info(f"Running batch inference job {job_name} with config: {config}")
            return create_batch_inference_job(
                s3_input_path,
                s3_inference_results_path,
                job_name,
                role_arn,
                solution_arn,
                num_results,
                config,
            )
        elif key.split("/")[-1] == "items.json":
            logger.info(f"Running batch segment job {job_name} for {num_users} users")
            return create_batch_segment_job(
                s3_input_path,
                s3_segment_results_path,
                job_name,
                num_users,
                role_arn,
                solution_arn,
            )
    except Exception as e:
        print(e)
        print(
            "Error getting object {} from bucket {}. Make sure they exist and your bucket is in "
            "the same region as this function.".format(key, bucket)
        )
        raise e
