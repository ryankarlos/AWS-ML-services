import boto3
import os
import urllib

personalize = boto3.client("personalize")


def lambda_handler(event, context):
    dataset_arn = os.environ["DATASET_ARN"]
    job_name = os.environ["JOB_NAME"]
    role_arn = os.environ["ROLE_ARN"]

    # Get the object from the event and show its content type
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    s3_input_path = f"s3://{bucket}/{key}"

    response = personalize.create_dataset_import_job(
        jobName=job_name,
        datasetArn=dataset_arn,
        dataSource={"dataLocation": s3_input_path},
        roleArn=role_arn,
    )

    dsij_arn = response["datasetImportJobArn"]

    print("Dataset Import Job arn: " + dsij_arn)

    description = personalize.describe_dataset_import_job(datasetImportJobArn=dsij_arn)[
        "datasetImportJob"
    ]

    print("Name: " + description["jobName"])
    print("ARN: " + description["datasetImportJobArn"])
    print("Status: " + description["status"])
    return response
