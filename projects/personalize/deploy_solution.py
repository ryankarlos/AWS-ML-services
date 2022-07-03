import boto3
import click

personalize = boto3.client("personalize")


@click.command()
@click.option(
    "--campaign_name", help="campaign name",
)
@click.option(
    "--sol_version_arn", help="solution version arn",
)
@click.option(
    "--config", help="campaign configuration",
)
@click.option(
    "--mode",
    default="create",
    type=click.Choice(["create", "update"]),
    help="whether to create new campaign or update existing campaign",
)
def deploy_solution(campaign_name, sol_version_arn, config, mode):
    if mode == "create":
        response = personalize.create_campaign(
            name=campaign_name,
            solutionVersionArn=sol_version_arn,
            minProvisionedTPS=1,
            campaignConfig={"itemExplorationConfig": config},
        )

    elif mode == "update":
        response = personalize.update_campaign(
            campaignArn=campaign_name,
            solutionVersionArn=sol_version_arn,
            minProvisionedTPS=1,
        )
    else:
        raise ValueError(
            f"mode must be either 'update' or 'create'. You passed in {mode}"
        )

    arn = response["campaignArn"]

    description = personalize.describe_campaign(campaignArn=arn)["campaign"]
    print("Name: " + description["name"])
    print("ARN: " + description["campaignArn"])
    print("Status: " + description["status"])

    return response


if __name__ == "__main__":
    deploy_solution()
