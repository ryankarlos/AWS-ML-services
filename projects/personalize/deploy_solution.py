import json

import boto3
import click
import logging
import sys

personalize = boto3.client("personalize")
logger = logging.getLogger("deploy")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


@click.command()
@click.option(
    "--campaign_name", default="MoviesCampaign", help="campaign name",
)
@click.option(
    "--sol_version_arn", help="solution version arn",
)
@click.option(
    "--config",
    default='{"itemExplorationConfig": {"explorationWeight": "0.3", "explorationItemAgeCutOff": "30"}}',
    help="campaign configuration",
)
@click.option(
    "--mode",
    default="create",
    type=click.Choice(["create", "update"]),
    help="whether to create new campaign or update existing campaign",
)
def deploy_solution(campaign_name, sol_version_arn, config, mode):
    """
    This is only required for real time recommendations
    :param campaign_name:
    :param sol_version_arn:
    :param config:
    :param mode:
    :return:
    """
    if mode == "create":
        config = json.loads(config)
        response = personalize.create_campaign(
            name=campaign_name,
            solutionVersionArn=sol_version_arn,
            minProvisionedTPS=1,
            campaignConfig=config,
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
    logger.info("Name: " + description["name"])
    logger.info("ARN: " + description["campaignArn"])
    logger.info("Status: " + description["status"])

    return response


if __name__ == "__main__":
    deploy_solution()
