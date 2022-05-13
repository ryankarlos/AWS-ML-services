import boto3
import json

sfn_client = boto3.client("stepfunctions")
iam_client = boto3.client("iam")


def deploy_step_function(role, definition_path="AWSNLPServicesdefinition.json"):
    with open(definition_path, "rb") as f:
        asl_definition = json.load(f)
    role = iam_client.get_role(RoleName=role)
    response = sfn_client.create_state_machine(
        name="ProcessTransactionStateMachine",
        definition=json.dumps(asl_definition),
        roleArn=role["Role"]["Arn"],
    )
    print(response)
    return response


def execute_state_machine(input, sf_name, deploy_sf=False, sf_role=None):
    sfn_list = sfn_client.list_state_machines()
    state_machine_arn = [
        k["stateMachineArn"] for k in sfn_list["stateMachines"] if k["name"] == sf_name
    ]
    if not state_machine_arn:
        if deploy_sf and sf_role is not None:
            deploy_step_function(sf_role)
        else:
            raise ValueError(
                f"No active step function resource with name '{sf_name}' exists. If you"
                f"need to create one pass in kwargs for 'definition_path' and 'role'"
            )
    print(
        f"list of state machines: \n\n {json.dumps(sfn_list['stateMachines'], indent=4, default=str)} \n"
    )
    print(f" state machine arn: {state_machine_arn[0]} \n")
    return sfn_client.start_execution(
        stateMachineArn=state_machine_arn[0], name=name, input=json.dumps(input)
    )
