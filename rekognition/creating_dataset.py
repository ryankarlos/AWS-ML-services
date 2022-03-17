import boto3
import argparse
import logging
import time
import json
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def create_dataset_from_existing_dataset(
    rek_client, project_arn, dataset_type, dataset_arn
):
    """
    Creates an Amazon Rekognition Custom Labels dataset using an existing dataset.
    :param rek_client: The Amazon Rekognition Custom Labels Boto3 client.
    :param project_arn: The ARN of the project in which you want to create a dataset.
    :param dataset_type: The type of the dataset that you want to create (train or test).
    :param dataset_arn: The ARN of the existing dataset that you want to use.
    """

    try:
        # Create the dataset

        dataset_type = dataset_type.upper()

        logger.info(
            f"Creating {dataset_type} dataset for project {project_arn} from dataset {dataset_arn}."
        )

        dataset_source = json.loads('{ "DatasetArn": "' + dataset_arn + '"}')

        response = rek_client.create_dataset(
            ProjectArn=project_arn,
            DatasetType=dataset_type,
            DatasetSource=dataset_source,
        )

        dataset_arn = response["DatasetArn"]

        logger.info(f"New dataset ARN: {dataset_arn}")

        finished = False
        while finished == False:

            dataset = rek_client.describe_dataset(DatasetArn=dataset_arn)

            status = dataset["DatasetDescription"]["Status"]

            if status == "CREATE_IN_PROGRESS":

                logger.info((f"Creating dataset: {dataset_arn} "))
                time.sleep(5)
                continue

            if status == "CREATE_COMPLETE":
                logger.info(f"Dataset created: {dataset_arn}")
                finished = True
                continue

            if status == "CREATE_FAILED":
                logger.exception(f"Dataset creation failed: {status} : {dataset_arn}")
                raise Exception(f"Dataset creation failed: {status} : {dataset_arn}")

            logger.exception(
                f"Failed. Unexpected state for dataset creation: {status} : {dataset_arn}"
            )
            raise Exception(
                f"Failed. Unexpected state for dataset creation: {status} : {dataset_arn}"
            )

        return dataset_arn

    except ClientError as err:
        logger.exception(f"Couldn't create dataset: {err.response['Error']['Message']}")
        raise


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument(
        "project_arn",
        help="The ARN of the project in which you want to create the dataset.",
    )

    parser.add_argument(
        "dataset_type",
        help="The type of the dataset that you want to create (train or test).",
    )

    parser.add_argument(
        "dataset_arn", help="The ARN of the dataset that you want to copy from."
    )


def main():

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:

        # get command line arguments
        parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
        add_arguments(parser)
        args = parser.parse_args()

        print(f"Creating {args.dataset_type} dataset for project {args.project_arn}")

        # Create the dataset
        rek_client = boto3.client("rekognition")

        dataset_arn = create_dataset_from_existing_dataset(
            rek_client, args.project_arn, args.dataset_type, args.dataset_arn
        )

        print(f"Finished creating dataset: {dataset_arn}")

    except ClientError as err:
        logger.exception(f"Problem creating dataset: {err}")
        print(f"Problem creating dataset: {err}")
    except Exception as err:
        logger.exception(f"Problem creating dataset: {err}")
        print(f"Problem creating dataset: {err}")


if __name__ == "__main__":
    main()
