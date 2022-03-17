import boto3
import argparse
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def create_project(rek_client, project_name):
    """
    Creates an Amazon Rekognition Custom Labels project
    :param rek_client: The Amazon Rekognition Custom Labels Boto3 client.
    :param project_name: A name for the new prooject.
    """

    try:
        # Create the project
        logger.info(f"Creating project: {project_name}")

        response = rek_client.create_project(ProjectName=project_name)

        logger.info(f"project ARN: {response['ProjectArn']}")

        return response["ProjectArn"]

    except ClientError as err:
        logger.exception(
            f"Couldn't create project - {project_name}: {err.response['Error']['Message']}"
        )
        raise


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument("project_name", help="A name for the new project.")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:

        # get command line arguments
        parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
        add_arguments(parser)
        args = parser.parse_args()

        print(f"Creating project: {args.project_name}")

        # Create the project
        rek_client = boto3.client("rekognition")

        project_arn = create_project(rek_client, args.project_name)

        print(f"Finished creating project: {args.project_name}")
        print(f"ARN: {project_arn}")

    except ClientError as err:
        logger.exception(f"Problem creating project: {err}")
        print(f"Problem creating project: {err}")


if __name__ == "__main__":
    main()
