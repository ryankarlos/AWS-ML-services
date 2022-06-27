import pprint
import boto3
from augmented_ai.fraud.constants import *
import json

pp = pprint.PrettyPrinter(indent=2)
s3 = boto3.client("s3")
a2i_runtime_client = boto3.client("sagemaker-a2i-runtime")
sagemaker = boto3.client("sagemaker")


def start_human_loop(human_loop_input, flow_def_arn):

    response = a2i_runtime_client.start_human_loop(
        HumanLoopName=humanLoopName,
        FlowDefinitionArn=flow_def_arn,
        HumanLoopInput={"InputContent": json.dumps(human_loop_input)},
    )
    return response


def check_human_loop_status(workteam_arn):
    workteamName = workteam_arn[workteam_arn.rfind("/") + 1 :]
    print(
        "Navigate to the private worker portal and do the tasks. Make sure you've invited yourself to your workteam!"
    )
    print(
        "https://"
        + sagemaker.describe_workteam(WorkteamName=workteamName)["Workteam"][
            "SubDomain"
        ]
    )
    return workteamName
