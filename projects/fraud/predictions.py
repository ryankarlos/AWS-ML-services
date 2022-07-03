import boto3
import click
import logging
import json
from logging import config
from augmented_ai.fraud.run_loop import start_human_loop, humanLoopName
import time

SCORE_THRESHOLD_MAX = 900
SCORE_THRESHOLD_MIN = 700
fraudDetector = boto3.client("frauddetector")
iam = boto3.resource("iam")


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


def parse_payload_from_json(payload_json_path):
    with open(payload_json_path) as f:
        payload = json.load(f)
    return payload


def real_time_predictions(
    payload,
    event_name="credit-card-fraud",
    detector_name="fraud_detector",
    detector_version="1",
):
    variables = payload["variables"]
    timestamp = payload["EVENT_TIMESTAMP"]
    event_id = payload["variables"]["trans_num"]
    flow_definition = payload["flow_definition"]
    entity_id = "unknown"
    entity_type = "customer"
    prediction_response = fraudDetector.get_event_prediction(
        detectorId=detector_name,
        eventId=event_id,
        detectorVersionId=detector_version,
        eventTypeName=event_name,
        eventTimestamp=timestamp,
        entities=[{"entityType": entity_type, "entityId": entity_id}],
        eventVariables=variables,
    )
    if flow_definition != "ignore":
        FraudScore = prediction_response["modelScores"][0]["scores"][
            "fraud_model_insightscore"
        ]
        if SCORE_THRESHOLD_MIN <= FraudScore <= SCORE_THRESHOLD_MAX:
            # Create the human loop input JSON object
            logger.info(
                f"fraud score {FraudScore} between range thresholds {SCORE_THRESHOLD_MAX} and {SCORE_THRESHOLD_MIN}"
            )
            human_loop_input = {
                "score": prediction_response["modelScores"][0]["scores"],
                "taskObject": payload,
            }
            logger.info(f"Started human loop: {humanLoopName}")
            augai_response = start_human_loop(human_loop_input, flow_definition)
            print("")
            print(augai_response)
    return prediction_response


def batch_predictions(
    s3input,
    s3output,
    event_name="credit-card-fraud",
    role_name="FraudDetectorRoleS3Access",
    detector_name="fraud_detector",
    detector_version=2,
):
    role = iam.Role(role_name)
    job_id = f"{event_name}-{str(int((time.time())))}"

    fraudDetector.create_batch_prediction_job(
        jobId=job_id,
        inputPath=s3input,
        outputPath=s3output,
        eventTypeName=event_name,
        detectorName=detector_name,
        detectorVersion=detector_version,
        iamRoleArn=role.arn,
    )
    time.sleep(5)
    response = fraudDetector.get_batch_prediction_jobs(jobId=job_id)
    return response


@click.command()
@click.option(
    "--predictions",
    type=click.Choice(["batch", "realtime"]),
    help="real or batch fraud predictions",
)
@click.option(
    "--s3input",
    "--option",
    default="",
    help="needs to be specified if using batch mode",
)
@click.option(
    "--s3output",
    "--option",
    default="",
    help="needs to be specified if using batch mode",
)
@click.option(
    "--payload_path",
    "--option",
    default="",
    help="needs to be specified if using realtime mode",
)
@click.option(
    "--event_name", "--option", default="credit_card_transaction", help="event name"
)
@click.option(
    "--detector_name", "--option", default="fraud_detector_demo", help="detector name"
)
@click.option(
    "--detector_version",
    "--option",
    default="2",
    help="Detector version. Realtime jobs require active status",
)
@click.option(
    "--role", "--option", default="FraudDetectorRoleS3Access", help="name of role"
)
def main(
    predictions,
    s3input,
    s3output,
    payload_path,
    event_name,
    detector_name,
    role,
    detector_version,
):
    if predictions == "batch":
        logger.info("running batch prediction job")
        if not s3input or not s3output:
            logger.error(
                "s3 input and s3 output paths need to be specified for batch mode"
            )
            raise
        response = batch_predictions(
            s3input, s3output, event_name, role, detector_name, detector_version
        )
        if response["batchPredictions"][0]["status"] in [
            "INPROGRESS",
            "IN_PROGRESS_INITIALIZING",
            "PENDING",
        ]:
            logger.info("Batch Job submitted successfully")
            print(response)
            return response
        else:
            logger.error("Batch job not submitted successfully as status not verified")
            raise
    elif predictions == "realtime":
        logger.info("running realtime prediction")
        if not payload_path:
            logger.error("payload json path need to be specified for realtime mode")
            raise
        payload = parse_payload_from_json(payload_path)
        response = real_time_predictions(
            payload, event_name, detector_name, detector_version
        )
        print("")
        print(json.dumps(response["modelScores"], default=str, indent=4))
        return response


if __name__ == "__main__":
    import boto3

    client = boto3.client("frauddetector")
    main()
    # response = fraudDetector.get_batch_prediction_jobs(jobId="credit-card-fraud-1655877151")
    # print(response)
