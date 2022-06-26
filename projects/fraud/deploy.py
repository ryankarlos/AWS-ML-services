import boto3
import click

fraudDetector = boto3.client("frauddetector")
DETECTOR_NAME = "fraud_detector_demo"
MODEL_NAME = "fraud_model"
MODEL_TYPE = "ONLINE_FRAUD_INSIGHTS"


def deploy_trained_model(version):
    fraudDetector.update_model_version_status(
        modelId=MODEL_NAME,
        modelType=MODEL_TYPE,
        modelVersionNumber=version,
        status="ACTIVE",
    )


def update_rule():
    client = boto3.client("frauddetector")
    client.update_rule_version(
        rule={"detectorId": DETECTOR_NAME, "ruleId": "investigate", "ruleVersion": "1"},
        expression=f"${MODEL_NAME}_insightscore > 900",
        language="DETECTORPL",
        outcomes=["high_risk"],
    )

    client.update_rule_version(
        rule={"detectorId": DETECTOR_NAME, "ruleId": "review", "ruleVersion": "1"},
        expression=f"${MODEL_NAME}_insightscore < 900 and ${MODEL_NAME}_insightscore > 700",
        language="DETECTORPL",
        outcomes=["medium_risk"],
    )

    client.update_rule_version(
        rule={"detectorId": DETECTOR_NAME, "ruleId": "approve", "ruleVersion": "1"},
        expression=f"${MODEL_NAME}_insightscore < 700",
        language="DETECTORPL",
        outcomes=["low_risk"],
    )


@click.command()
@click.option(
    "--update_rule",
    "--option",
    default="false",
    type=click.Choice(["true", "false"]),
    help="whether to update detector business rules",
)
@click.option(
    "--version",
    "--option",
    default="1.0",
    help="model version to deploy",
)
def main(update_rule, version):
    if update_rule == "true":
        update_rule()
    deploy_trained_model(version=version)


if __name__ == "__main__":
    main()
