import boto3
import io
import logging
import argparse
from PIL import Image, ImageDraw, ImageFont
from botocore.exceptions import ClientError
import time

logger = logging.getLogger(__name__)


rek_client = boto3.client("rekognition")


logger = logging.getLogger(__name__)


def start_model(rek_client, project_arn, model_arn, min_inference_units):
    """
    Copied from https://docs.aws.amazon.com/rekognition/latest/customlabels-dg/rm-start.html#rm-start-sdk
    """

    try:
        # Start the model
        logger.info(f"Starting model: {model_arn}. Please wait....")

        rek_client.start_project_version(
            ProjectVersionArn=model_arn, MinInferenceUnits=min_inference_units
        )

        # Wait for the model to be in the running state
        version_name = (model_arn.split("version/", 1)[1]).rpartition("/")[0]
        project_version_running_waiter = rek_client.get_waiter(
            "project_version_running"
        )
        project_version_running_waiter.wait(
            ProjectArn=project_arn, VersionNames=[version_name]
        )

        # Get the running status
        return get_model_status(rek_client, project_arn, model_arn)

    except Exception as e:
        logger.exception(
            f"Couldn't start model - {model_arn}: {e.response['Error']['Message']}"
        )

    print("Done...")


def get_model_status(rek_client, project_arn, model_arn):
    """
    Gets the current status of an Amazon Rekognition Custom Labels model
    :param rek_client: The Amazon Rekognition Custom Labels Boto3 client.
    :param project_name:  The name of the project that you want to use.
    :param model_arn:  The name of the model that you want the status for.
    """

    logger.info(f"Getting status for {model_arn}.")

    # extract the model version from the model arn.
    version_name = (model_arn.split("version/", 1)[1]).rpartition("/")[0]

    models = rek_client.describe_project_versions(
        ProjectArn=project_arn, VersionNames=[version_name]
    )

    for model in models["ProjectVersionDescriptions"]:
        logger.info(f"Status: {model['StatusMessage']}")
        return model["Status"]

    logger.exception(f"Model {model_arn} not found.")
    raise Exception(f"Model {model_arn} not found.")


def stop_model(rek_client, project_arn, model_arn):
    """
    Stops a running Amazon Rekognition Custom Labels Model.
    :param rek_client: The Amazon Rekognition Custom Labels Boto3 client.
    :param project_arn: The ARN of the project that you want to stop running.
    :param model_arn:  The ARN of the model (ProjectVersion) that you want to stop running.
    """

    logger.info(f"Stopping model: {model_arn}")

    try:
        # Stop the model
        response = rek_client.stop_project_version(ProjectVersionArn=model_arn)

        logger.info(f"Status: {response['Status']}")

        # stops when hosting has stopped or failure.
        status = ""
        finished = False

        while finished is False:

            status = get_model_status(rek_client, project_arn, model_arn)

            if status == "STOPPING":
                logger.info("Model stopping in progress...")
                time.sleep(10)
                continue
            if status == "STOPPED":
                logger.info("Model is not running.")
                finished = True
                continue

            logger.exception(f"Error stopping model. Unexepected state: {status}")
            raise Exception(f"Error stopping model. Unexepected state: {status}")

        logger.info(f"finished. Status {status}")
        return status

    except ClientError as e:
        logger.exception(
            f"Couldn't stop model - {model_arn}: {e.response['Error']['Message']}"
        )
        raise


def analyze_local_image(rek_client, model, photo, min_confidence):
    """
    Analyzes an image stored as a local file.
    :param rek_client: The Amazon Rekognition Boto3 client.
    :param s3_connection: The Amazon S3 Boto3 S3 connection object.
    :param model: The ARN of the Amazon Rekognition Custom Labels model that you want to use.
    :param photo: The name and file path of the photo that you want to analyze.
    :param min_confidence: The desired threshold/confidence for the call.
    """

    try:
        logger.info("Analyzing local file: %s", photo)
        image = Image.open(photo)
        image_type = Image.MIME[image.format]

        if (image_type == "image/jpeg" or image_type == "image/png") == False:
            logger.error("Invalid image type for %s", photo)
            raise ValueError(
                f"Invalid file format. Supply a jpeg or png format file: {photo}"
            )

        # get images bytes for call to detect_anomalies
        image_bytes = io.BytesIO()
        image.save(image_bytes, format=image.format)
        image_bytes = image_bytes.getvalue()

        response = rek_client.detect_custom_labels(
            Image={"Bytes": image_bytes},
            MinConfidence=min_confidence,
            ProjectVersionArn=model,
        )

        show_predictions(image, response)
        return len(response["CustomLabels"])

    except ClientError as client_err:
        logger.error(format(client_err))
        raise
    except FileNotFoundError as file_error:
        logger.error(format(file_error))
        raise


def analyze_s3_image(rek_client, s3_connection, model, bucket, photo, min_confidence):
    """
    Analyzes an image stored in the specified S3 bucket.
    :param rek_client: The Amazon Rekognition Boto3 client.
    :param s3_connection: The Amazon S3 Boto3 S3 connection object.
    :param model: The ARN of the Amazon Rekognition Custom Labels model that you want to use.
    :param bucket: The name of the S3 bucket that contains the image that you want to analyze.
    :param photo: The name of the photo that you want to analyze.
    :param min_confidence: The desired threshold/confidence for the call.
    """

    try:
        # Get image from S3 bucket.

        logger.info("analyzing bucket: %s image: %s", bucket, photo)
        s3_object = s3_connection.Object(bucket, photo)
        s3_response = s3_object.get()

        stream = io.BytesIO(s3_response["Body"].read())
        image = Image.open(stream)

        image_type = Image.MIME[image.format]

        if (image_type == "image/jpeg" or image_type == "image/png") == False:
            logger.error("Invalid image type for %s", photo)
            raise ValueError(
                f"Invalid file format. Supply a jpeg or png format file: {photo}"
            )

        img_width, img_height = image.size
        draw = ImageDraw.Draw(image)

        # Call DetectCustomLabels
        response = rek_client.detect_custom_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": photo}},
            MinConfidence=min_confidence,
            ProjectVersionArn=model,
        )

        show_predictions(image, response)
        return len(response["CustomLabels"])

    except ClientError as err:
        logger.error(format(err))
        raise


def show_predictions(response):
    """
    Displays the analyzed image and overlays analysis results
    :param image: The analyzed image
    :param response: the response from DetectCustomLabels
    """
    try:
        for custom_label in response["CustomLabels"]:
            confidence = int(round(custom_label["Confidence"], 0))
            logger.info(f"{custom_label['Name']}:{confidence}%")
    except Exception as err:
        logger.error(format(err))
        raise


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument("model_arn", help="The ARN of the model that you want to use.")

    parser.add_argument(
        "image", help="The path and file name of the image that you want to analyze"
    )
    parser.add_argument(
        "--bucket",
        help="The bucket that contains the image. If not supplied, image is assumed to be a local file.",
        required=False,
    )


def main():
    try:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

        # get command line arguments
        parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
        add_arguments(parser)
        args = parser.parse_args()

        label_count = 0
        min_confidence = 50

        rek_client = boto3.client("rekognition")

        if args.bucket == None:
            # Analyze local image
            label_count = analyze_local_image(
                rek_client, args.model_arn, args.image, min_confidence
            )
        else:
            # Analyze image in S3 bucket
            s3_connection = boto3.resource("s3")
            label_count = analyze_s3_image(
                rek_client,
                s3_connection,
                args.model_arn,
                args.bucket,
                args.image,
                min_confidence,
            )

        print(f"Custom labels detected: {label_count}")

    except ClientError as client_err:
        print(
            "A service client error occurred: "
            + format(client_err.response["Error"]["Message"])
        )

    except ValueError as value_err:
        print("A value error occurred: " + format(value_err))

    except FileNotFoundError as file_error:
        print("File not found error: " + format(file_error))

    except Exception as err:
        print("An error occurred: " + format(err))


if __name__ == "__main__":
    main()
