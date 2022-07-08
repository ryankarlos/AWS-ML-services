import os
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client("stepfunctions")

sfnName = os.environ["SFN_NAME"]
s3_input = os.environ["S3_INPUT"]
solution_arn = os.environ["SOLUTION_ARN"]
dataset_group_arn = os.environ["DATASET_GROUP_ARN"]
dataset_arn = os.environ["DATASET_ARN"]
role_arn = os.environ["ROLE_ARN"]
recipe_arn = os.environ["RECIPE_ARN"]

sfn_input = {
    "S3input": s3_input,
    "SolutionArn": solution_arn,
    "DatasetGroupArn": dataset_group_arn,
    "DatasetArn": dataset_arn,
    "RoleArn": role_arn,
    "RecipeArn": recipe_arn,
}


def lambda_handler(event, context):
    logger.info("## INITIATED BY S3 notification EVENT: ")
    response = client.start_execution(name=sfnName, input=json.dumps(sfn_input))
    logger.info("## STARTED STEP FUNCTION EXECUTION: " + response["executionArn"])
    print(response)
    return response
