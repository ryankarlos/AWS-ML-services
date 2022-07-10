import os
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client("stepfunctions")

sfn_name = os.environ["SFN_NAME"]
s3_input = os.environ["S3_INPUT"]
solution_arn = os.environ["SOLUTION_ARN"]
solution_name = os.environ["SOLUTION_NAME"]
dataset_group_arn = os.environ["DATASET_GROUP_ARN"]
dataset_arn = os.environ["DATASET_ARN"]
role_arn = os.environ["ROLE_ARN"]
recipe_arn = os.environ["RECIPE_ARN"]

sfn_input = {
    "S3input": s3_input,
    "SolutionArn": solution_arn,
    "SolutionName": solution_name,
    "DatasetGroupArn": dataset_group_arn,
    "DatasetArn": dataset_arn,
    "RoleArn": role_arn,
    "RecipeArn": recipe_arn,
}


def lambda_handler(event, context):
    logger.info("## INITIATED BY S3 notification EVENT: ")
    response = client.list_state_machines()
    sfn_arn = [
        sfn["stateMachineArn"]
        for sfn in response["stateMachines"]
        if sfn["name"] == sfn_name
    ][0]
    print(f"State machine arn {sfn_arn} for name {sfn_name}")
    response = client.start_execution(
        stateMachineArn=sfn_arn, input=json.dumps(sfn_input)
    )
    logger.info("## STARTED STEP FUNCTION EXECUTION: " + response["executionArn"])
