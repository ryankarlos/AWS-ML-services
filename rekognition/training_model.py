import boto3
import argparse
import logging
import json
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

rek_client = boto3.client("rekognition")


def train_model(
    rek_client,
    project_arn,
    version_name,
    output_bucket,
    output_folder,
    tag_key,
    tag_key_value,
):
    """
    Trains an Amazon Rekognition Custom Labels model.
    :param rek_client: The Amazon Rekognition Custom Labels Boto3 client.
    :param project_arn: The ARN of the project in which you want to train a model.
    :param version_name: A version for the model.
    :param output_bucket: The S3 bucket that hosts training output.
    :param output_folder: The path for the training output within output_bucket
    :param tag_key: The name of a tag to attach to the model. Pass None to exclude
    :param tag_key_value: The value of the tag. Pass None to exclude

    """

    try:
        # Train the model

        status = ""
        logger.info(f"training model version {version_name} for project {project_arn}")

        output_config = json.loads(
            '{"S3Bucket": "'
            + output_bucket
            + '", "S3KeyPrefix": "'
            + output_folder
            + '" }  '
        )

        tags = {}

        if tag_key != None and tag_key_value != None:
            tags = json.loads('{"' + tag_key + '":"' + tag_key_value + '"}')

        response = rek_client.create_project_version(
            ProjectArn=project_arn,
            VersionName=version_name,
            OutputConfig=output_config,
            Tags=tags,
        )

        logger.info(f"Started training: {response['ProjectVersionArn']}")

        # Wait for the project version training to complete

        project_version_training_completed_waiter = rek_client.get_waiter(
            "project_version_training_completed"
        )
        project_version_training_completed_waiter.wait(
            ProjectArn=project_arn, VersionNames=[version_name]
        )

        # Get the completion status
        describe_response = rek_client.describe_project_versions(
            ProjectArn=project_arn, VersionNames=[version_name]
        )
        for model in describe_response["ProjectVersionDescriptions"]:
            logger.info("Status: " + model["Status"])
            logger.info("Message: " + model["StatusMessage"])
            status = model["Status"]

        logger.info(f"finished training")

        return response["ProjectVersionArn"], status

    except ClientError as err:
        logger.exception(f"Couldn't create dataset: {err.response['Error']['Message']}")
        raise


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument(
        "project_arn", help="The ARN of the project in which you want to train a model"
    )

    parser.add_argument("version_name", help="A version name of your choosing.")

    parser.add_argument(
        "output_bucket", help="The S3 bucket that receives the training results."
    )

    parser.add_argument(
        "output_folder",
        help="The folder in the S3 bucket where training results are stored.",
    )

    parser.add_argument(
        "--tag_name", help="The name of a tag to attach to the model", required=False
    )

    parser.add_argument("--tag_value", help="The value for the tag.", required=False)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:

        # get command line arguments
        parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
        add_arguments(parser)
        args = parser.parse_args()

        print(
            f"Training model version {args.version_name} for project {args.project_arn}"
        )

        # Train the model
        rek_client = boto3.client("rekognition")

        model_arn, status = train_model(
            rek_client,
            args.project_arn,
            args.version_name,
            args.output_bucket,
            args.output_folder,
            args.tag_name,
            args.tag_value,
        )

        print(f"Finished training model: {model_arn}")
        print(f"Status: {status}")

    except ClientError as err:
        logger.exception(f"Problem training model: {err}")
        print(f"Problem training model: {err}")
    except Exception as err:
        logger.exception(f"Problem training model: {err}")
        print(f"Problem training model: {err}")


if __name__ == "__main__":
    main()
