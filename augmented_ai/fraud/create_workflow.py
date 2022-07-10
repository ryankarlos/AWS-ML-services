import boto3
from augmented_ai.fraud.constants import *
import click

sagemaker = boto3.client("sagemaker")
iam = boto3.client("iam")
role_arn = iam.get_role(RoleName=ROLE)["Role"]["Arn"]


def create_task_ui(task_ui_name, template):
    """
    Creates a Human Task UI resource.

    Returns:
    struct: HumanTaskUiArn
    """
    response = sagemaker.create_human_task_ui(
        HumanTaskUiName=task_ui_name, UiTemplate={"Content": template}
    )
    human_task_arn = response["HumanTaskUiArn"]
    print(f"Created human task ui with Arn: {human_task_arn}")
    return human_task_arn


def create_flow_definition(flow_definition_name, human_task_arn, workteam_arn):
    """
    Creates a Flow Definition resource

    Returns:
    struct: FlowDefinitionArn
    """
    response = sagemaker.create_flow_definition(
        FlowDefinitionName=flow_definition_name,
        RoleArn=role_arn,
        HumanLoopConfig={
            "WorkteamArn": workteam_arn,
            "HumanTaskUiArn": human_task_arn,
            "TaskCount": 1,
            "TaskDescription": "Please review the  data and flag for potential fraud",
            "TaskTitle": " Review and Approve / Reject Amazon Fraud detector predictions. ",
        },
        OutputConfig={"S3OutputPath": BUCKET},
    )
    flow_def_arn = response["FlowDefinitionArn"]
    print(f"Created flow definition with Arn: {flow_def_arn}")

    return flow_def_arn


@click.command()
@click.option(
    "--workteam_arn",
    "--option",
    help="real or batch fraud predictions",
)
def main(workteam_arn):
    human_task_arn = create_task_ui(taskUIName, fraud_template)
    flow_def_arn = create_flow_definition(
        flowDefinitionName, human_task_arn, workteam_arn
    )
    return flow_def_arn, human_task_arn


if __name__ == "__main__":
    main()
