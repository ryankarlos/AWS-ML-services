import re
import pprint
import boto3
from augmented_ai.fraud.constants import *
import json

pp = pprint.PrettyPrinter(indent=2)
s3 = boto3.client("s3")
a2i_runtime_client = boto3.client("sagemaker-a2i-runtime")
sagemaker = boto3.client("sagemaker")


def retrieve_a2i_results_from_output_s3_uri(bucket, a2i_s3_output_uri):
    """
    Gets the json file published by A2I and returns a deserialized object
    """
    splitted_string = re.split("s3://" + bucket + "/", a2i_s3_output_uri)
    output_bucket_key = splitted_string[1]

    response = s3.get_object(Bucket=bucket, Key=output_bucket_key)
    content = response["Body"].read()
    return json.loads(content)


def evaluate_results(completed_loops):
    for human_loop_name in completed_loops:
        describe_human_loop_response = a2i_runtime_client.describe_human_loop(
            HumanLoopName=human_loop_name
        )

        print(f'\nHuman Loop Name: {describe_human_loop_response["HumanLoopName"]}')
        print(f'Human Loop Status: {describe_human_loop_response["HumanLoopStatus"]}')
        print(
            f'Human Loop Output Location: : {describe_human_loop_response["HumanLoopOutput"]["OutputS3Uri"]} \n'
        )

        # Uncomment below line to print out a2i human answers
        pp.pprint(
            retrieve_a2i_results_from_output_s3_uri(
                BUCKET, describe_human_loop_response["HumanLoopOutput"]["OutputS3Uri"]
            )
        )
