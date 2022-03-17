import boto3
import argparse
import logging
import time
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
rek_client = boto3.client("rekognition")


def delete_model(rek_client, project_arn, model_arn):
    """
    Deletes an Amazon Rekognition Custom Labels model.
    :param rek_client: The Amazon Rekognition Custom Labels Boto3 client.
    :param model_arn: The ARN of the model version that you want to delete.
    """

    try:
        # Delete the model
        logger.info(f"Deleting dataset: {model_arn}")

        rek_client.delete_project_version(ProjectVersionArn=model_arn)

        # Get the model version name
        start = find_forward_slash(model_arn, 3) + 1
        end = find_forward_slash(model_arn, 4)
        version_name = model_arn[start:end]

        deleted = False

        # model might not be deleted yet, so wait deletion finishes.
        while not deleted:
            describe_response = rek_client.describe_project_versions(
                ProjectArn=project_arn, VersionNames=[version_name]
            )
            if len(describe_response["ProjectVersionDescriptions"]) == 0:
                deleted = True
            else:
                logger.info(f"Waiting for model deletion {model_arn}")
                time.sleep(5)

        logger.info(f"model deleted: {model_arn}")

        return True

    except ClientError as err:
        logger.exception(
            f"Couldn't delete model - {model_arn}: {err.response['Error']['Message']}"
        )
        raise


def confirm_model_deletion(model_arn):
    """
    Confirms deletion of the model. Returns True if delete entered.
    :param model_arn: The ARN of the model that you want to delete.
    """
    print(f"Are you sure you wany to delete model {model_arn} ?\n", model_arn)

    start = input("Enter delete to delete your model: ")
    if start == "delete":
        return True
    else:
        return False


def delete_dataset(rek_client, dataset_arn):
    """
    Deletes an Amazon Rekognition Custom Labels dataset.
    :param rek_client: The Amazon Rekognition Custom Labels Boto3 client.
    :param dataset_arn: The ARN of the dataset that you want to delete.
    """

    try:
        # Delete the dataset
        logger.info(f"Deleting dataset: {dataset_arn}")

        rek_client.delete_dataset(DatasetArn=dataset_arn)

        deleted = False

        logger.info(f"waiting for dataset deletion {dataset_arn}")

        # dataset might not be deleted yet, so wait.
        while not deleted:
            try:
                rek_client.describe_dataset(DatasetArn=dataset_arn)
                time.sleep(5)
            except ClientError as err:
                if err.response["Error"]["Code"] == "ResourceNotFoundException":
                    logger.info(f"dataset deleted: {dataset_arn}")
                    deleted = True
                else:
                    raise

        logger.info(f"dataset deleted: {dataset_arn}")

        return True

    except ClientError as err:
        logger.exception(
            f"Couldn't delete dataset - {dataset_arn}: {err.response['Error']['Message']}"
        )
        raise


def find_forward_slash(input_string, n):
    """
    Returns the location of '/' after n number of occurences.
    :param input_string: The string you want to search
    : n: the occurence that you want to find.
    """
    position = input_string.find("/")
    while position >= 0 and n > 1:
        position = input_string.find("/", position + 1)
        n -= 1
    return position


def delete_project(rek_client, project_arn):
    """
    Deletes an Amazon Rekognition Custom Labels project.
    :param rek_client: The Amazon Rekognition Custom Labels Boto3 client.
    :param project_arn: The ARN of the project that you want to delete.
    """

    try:
        # Delete the project
        logger.info(f"Deleting project: {project_arn}")

        response = rek_client.delete_project(ProjectArn=project_arn)

        logger.info(f"project status: {response['Status']}")

        deleted = False

        logger.info(f"waiting for project deletion {project_arn}")

        # Get the project name
        start = find_forward_slash(project_arn, 1) + 1
        end = find_forward_slash(project_arn, 2)
        project_name = project_arn[start:end]

        project_names = [project_name]

        while not deleted:

            project_descriptions = rek_client.describe_projects(
                ProjectNames=project_names
            )["ProjectDescriptions"]

            if len(project_descriptions) == 0:
                deleted = True

            else:
                time.sleep(5)

        logger.info(f"project deleted: {project_arn}")

        return True

    except ClientError as err:
        logger.exception(
            f"Couldn't delete project - {project_arn}: {err.response['Error']['Message']}"
        )
        raise


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument(
        "--resource",
        choices=["dataset", "project", "model"],
        help="The type of resource that needs deletion.",
    )

    parser.add_argument(
        "--dataset_arn",
        help="The ARN of the dataset that you want to delete.",
        required=False,
    )

    parser.add_argument(
        "--project_arn",
        help="The ARN of the project that contains the model that you want to delete.",
        required=False,
    )

    parser.add_argument(
        "--model_arn",
        help="The ARN of the model version that you want to delete.",
        required=False,
    )


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # get command line arguments
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    add_arguments(parser)
    args = parser.parse_args()
    try:

        if args.resource == "model":
            expected_arns = {"model_arn", "project_arn"}
            if expected_arns.issubset(args.keys):

                if confirm_model_deletion(args.model_arn):
                    logger.info(f"Deleting model: {args.model_arn}")

                    delete_model(rek_client, args.project_arn, args.model_arn)

                    logger.info(f"Finished deleting model: {args.model_arn}")
                else:
                    logger.info(f"Not deleting model {args.model_arn}")

                logger.info(f"Deleting dataset: {args.dataset_arn}")
            else:
                raise ValueError(
                    "Model and project arns needs to be passed for deleting model"
                )

        elif args.resource == "dataset":
            expected_arns = {"dataset_arn"}
            if expected_arns.issubset(args.keys):
                delete_dataset(rek_client, args.dataset_arn)

                logger.info(f"Finished deleting dataset: {args.dataset_arn}")
            else:
                raise ValueError(
                    "Model and project arns needs to be passed for deleting model"
                )

        elif args.resource == "project":
            expected_arns = {"project_arn"}
            if expected_arns.issubset(args.keys):
                delete_project(rek_client, args.project_arn)

                logger.info(f"Finished deleting project: {args.project_arn}")
            else:
                raise ValueError(
                    "Model and project arns needs to be passed for deleting model"
                )

    except ClientError as err:
        logger.exception(f"Problem deleting {args.resource}: {err}")


if __name__ == "__main__":
    main()
