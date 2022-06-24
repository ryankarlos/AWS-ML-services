import boto3
import click

fraudDetector = boto3.client("frauddetector")
DETECTOR_NAME = "fraud_detector_demo"
MODEL_NAME = "fraud_model"
MODEL_TYPE = "ONLINE_FRAUD_INSIGHTS"


def deploy_trained_model(model_name, version="1.0"):
    fraudDetector.update_model_version_status(
        modelId=model_name,
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
def main(update_rule):
    if update_rule == "true":
        update_rule()
    deploy_trained_model(model_name="fraud_model")


if __name__ == "__main__":
    main()
