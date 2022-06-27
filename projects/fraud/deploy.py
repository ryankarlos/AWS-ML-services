import boto3
import click
import json
import logging
from logging import config

fraudDetector = boto3.client("frauddetector")
DETECTOR_NAME = "fraud_detector_demo"
MODEL_NAME = "fraud_model"
MODEL_TYPE = "ONLINE_FRAUD_INSIGHTS"


log_config = {
    "version": 1,
    "root": {"handlers": ["console"], "level": "INFO"},
    "handlers": {
        "console": {
            "formatter": "std_out",
            "class": "logging.StreamHandler",
            "level": "INFO",
        }
    },
    "formatters": {
        "std_out": {
            "format": "%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(lineno)d : %(message)s",
            "datefmt": "%d-%m-%Y %I:%M:%S",
        }
    },
}

config.dictConfig(log_config)

logger = logging.getLogger(__name__)


def deploy_trained_model(model_version, rules_version):
    model_version = [
        {
            "modelId": MODEL_NAME,
            "modelType": MODEL_TYPE,
            "modelVersionNumber": model_version,
        }
    ]
    rules = [
        {
            "detectorId": DETECTOR_NAME,
            "ruleId": "investigate",
            "ruleVersion": rules_version,
        },
        {"detectorId": DETECTOR_NAME, "ruleId": "review", "ruleVersion": rules_version},
        {
            "detectorId": DETECTOR_NAME,
            "ruleId": "approve",
            "ruleVersion": rules_version,
        },
    ]
    response = fraudDetector.create_detector_version(
        detectorId=DETECTOR_NAME, modelVersions=model_version, rules=rules
    )
    return response


def update_detector_rules(rule_version):
    client = boto3.client("frauddetector")
    logging.info("Updating Investigate rule ....")
    response1 = client.update_rule_version(
        rule={
            "detectorId": DETECTOR_NAME,
            "ruleId": "investigate",
            "ruleVersion": rule_version,
        },
        expression=f"${MODEL_NAME}_insightscore > 900",
        language="DETECTORPL",
        outcomes=["high_risk"],
    )
    print(response1["rule"])
    print("")
    logging.info("Updating review rule ....")
    response2 = client.update_rule_version(
        rule={
            "detectorId": DETECTOR_NAME,
            "ruleId": "review",
            "ruleVersion": rule_version,
        },
        expression=f"${MODEL_NAME}_insightscore < 900 and ${MODEL_NAME}_insightscore > 700",
        language="DETECTORPL",
        outcomes=["medium_risk"],
    )
    print(response2["rule"])
    print("")
    logging.info("Updating approve rule ....")
    response3 = client.update_rule_version(
        rule={
            "detectorId": DETECTOR_NAME,
            "ruleId": "approve",
            "ruleVersion": rule_version,
        },
        expression=f"${MODEL_NAME}_insightscore < 700",
        language="DETECTORPL",
        outcomes=["low_risk"],
    )
    print(response3["rule"])
    print("")


@click.command()
@click.option(
    "--update_rule",
    "--option",
    default="",
    help="Pass in rule version number e.g. 1 to update",
)
@click.option(
    "--model_version",
    "--option",
    default="1.0",
    help="model version to associate with detector",
)
@click.option(
    "--rules_version",
    "--option",
    default="2",
    help="rule version to associate with detector",
)
def main(update_rule, rules_version, model_version):
    if update_rule:
        logging.info(f"Updating rule version {update_rule}")
        update_detector_rules(update_rule)
    logging.info(
        f"Deploying trained model version {model_version} to new detector version "
    )
    response = deploy_trained_model(model_version, rules_version)
    print(response)


if __name__ == "__main__":
    main()
