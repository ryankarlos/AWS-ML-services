import boto3
import json
import os
from pathlib import Path
import time


sfn_client = boto3.client("stepfunctions")
iam_client = boto3.client("iam")


def deploy_step_function(role, sf_name, filename="AWSNLPServicesdefinition.json"):
    parent_dir = Path(__file__).parent.absolute()
    os.chdir(parent_dir)
    with open(os.path.join(str(parent_dir), filename), "rb") as f:
        asl_definition = json.load(f)
    role = iam_client.get_role(RoleName=role)
    response = sfn_client.create_state_machine(
        name=sf_name,
        definition=json.dumps(asl_definition),
        roleArn=role["Role"]["Arn"],
    )
    return response


def execute_state_machine(sf_input, sf_name, deploy_sf=False, sf_role=None):
    if deploy_sf and sf_role is not None:
        print("\nDeploying step function: \n")
        response = deploy_step_function(sf_role, sf_name)
        print(json.dumps(response,  indent=4, default=str))
        print("\n waiting for 30 secs for deployment to complete and state function in active state \n")
        time.sleep(30)
    sfn_list = sfn_client.list_state_machines()
    state_machine_arn = [
        k["stateMachineArn"] for k in sfn_list["stateMachines"] if k["name"] == sf_name
    ]
    if not state_machine_arn:
        raise ValueError(
            f"No active step function resource with name '{sf_name}' exists. If you"
            f"need to create one pass in kwargs for 'definition_path' and 'role'"
        )
    print(f"Step function '{sf_name}' is active with resource arn: {state_machine_arn[0]} \n")
    response = sfn_client.start_execution(
        stateMachineArn=state_machine_arn[0], input=json.dumps(sf_input)
    )
    print(f"Executed state machine {sf_name}: \n {json.dumps(response, indent=4, default=str)} \n")
    execution_status = "RUNNING"
    bad_status = ['FAILED', 'TIMED_OUT', 'ABORTED']
    while execution_status == "RUNNING":
        print(f"Execution status is 'RUNNING', waiting 10 secs before checking status again")
        time.sleep(10)
        execution_status = sfn_client.describe_execution(executionArn=response['executionArn'])['status']
        if execution_status in bad_status:
            print(f'Job did not succeed with status {execution_status}')
            break
        elif execution_status == "SUCCEEDED":
            print(f'Job succeeded !')
            break





