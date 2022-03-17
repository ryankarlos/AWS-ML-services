import boto3
import logging
import argparse
from botocore.exceptions import ClientError
import io
from PIL import Image, ImageDraw, ExifTags, ImageColor, ImageFont


rek_client = boto3.client("rekognition")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def start_model(project_arn, model_arn, version_name, min_inference_units):
    client = boto3.client("rekognition")

    try:
        # Start the model
        print("Starting model: " + model_arn)
        response = client.start_project_version(
            ProjectVersionArn=model_arn, MinInferenceUnits=min_inference_units
        )
        # Wait for the model to be in the running state
        project_version_running_waiter = client.get_waiter("project_version_running")
        project_version_running_waiter.wait(
            ProjectArn=project_arn, VersionNames=[version_name]
        )

        # Get the running status
        describe_response = client.describe_project_versions(
            ProjectArn=project_arn, VersionNames=[version_name]
        )
        for model in describe_response["ProjectVersionDescriptions"]:
            print("Status: " + model["Status"])
            print("Message: " + model["StatusMessage"])
    except Exception as e:
        print(e)

    print("Done...")


def stop_model(model_arn):

    client = boto3.client("rekognition")

    print("Stopping model:" + model_arn)

    # Stop the model
    try:
        response = client.stop_project_version(ProjectVersionArn=model_arn)
        status = response["Status"]
        print("Status: " + status)
    except Exception as e:
        print(e)

    print("Done...")


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

        if not (image_type == "image/jpeg" or image_type == "image/png"):
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
        logger.info(f"Detected custom labels for {photo}: {response['CustomLabels']}")

        # For object detection use case, uncomment below code to display image.
        # image = draw_bounding_box_for_labels(response, image)

        return response, image
    except ClientError as client_err:
        logger.error(format(client_err))
        raise
    except FileNotFoundError as file_error:
        logger.error(format(file_error))
        raise


def analyze_s3_image(rek_client, bucket, photo, model_arn, min_confidence):
    # Load image from S3 bucket
    s3_connection = boto3.resource("s3")

    s3_object = s3_connection.Object(bucket, photo)
    s3_response = s3_object.get()

    stream = io.BytesIO(s3_response["Body"].read())
    image = Image.open(stream)
    # Call DetectCustomLabels
    response = rek_client.detect_custom_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": photo}},
        MinConfidence=min_confidence,
        ProjectVersionArn=model_arn,
    )

    # For object detection use case, uncomment below code to display image.
    # image = draw_bounding_box_for_labels(response, image)

    return response, image


def draw_bounding_box_for_labels(response, image):
    # calculate and display bounding boxes for each detected custom label
    imgWidth, imgHeight = image.size
    draw = ImageDraw.Draw(image)
    for customLabel in response["CustomLabels"]:
        print("Label " + str(customLabel["Name"]))
        print("Confidence " + str(customLabel["Confidence"]))
        if "Geometry" in customLabel:
            box = customLabel["Geometry"]["BoundingBox"]
            left = imgWidth * box["Left"]
            top = imgHeight * box["Top"]
            width = imgWidth * box["Width"]
            height = imgHeight * box["Height"]

            fnt = ImageFont.truetype("/Library/Fonts/Arial.ttf", 50)
            draw.text((left, top), customLabel["Name"], fill="#00d400", font=fnt)

            print("Left: " + "{0:.0f}".format(left))
            print("Top: " + "{0:.0f}".format(top))
            print("Label Width: " + "{0:.0f}".format(width))
            print("Label Height: " + "{0:.0f}".format(height))

            points = (
                (left, top),
                (left + width, top),
                (left + width, top + height),
                (left, top + height),
                (left, top),
            )
            draw.line(points, fill="#00d400", width=5)

    return image


def add_arguments():
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """
    # get command line arguments
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    add_arguments(parser)
    args = parser.parse_args()
    parser.add_argument(
        "--model_arn", help="The ARN of the model that you want to use."
    )
    parser.add_argument(
        "--project_arn",
        help="The ARN of the project that contains that the model you want to start.",
    )
    parser.add_argument(
        "--image", help="The path and file name of the image that you want to analyze"
    )
    parser.add_argument(
        "--min_inference_units",
        default=1,
        help="The minimum number of inference units to use.",
    )
    parser.add_argument(
        "--min_confidence",
        default=50,
        help="Min confidence threshold for label detection",
    )
    parser.add_argument(
        "--bucket",
        help="The bucket that contains the image. If not supplied, image is assumed to be a local file.",
        required=False,
    )
    parser.add_argument(
        "--photo",
        help="the image key for the image if fetching from s3 bucket",
        required=False,
    )

    return args


def main():
    try:
        args = add_arguments()

        # start the model
        start_model(
            args.project_arn,
            args.model_arn,
            args.version_name,
            args.min_inference_units,
        )
        logger.info(f"Finished starting model: {args.model_arn}")

        if args.bucket is None:
            # Analyze local image
            logger.info(f"Analysing local image as --bucket arg not supplied")
            _, image = analyze_local_image(
                rek_client, args.model_arn, args.image, args.min_confidence
            )
            image.show()
        else:
            # Analyze image in S3 bucket
            if args.photo is None:
                raise ValueError(
                    f"--photo arg also needs to be supplied if fetching image from s3 bucket"
                )
            _, image = analyze_s3_image(
                rek_client, args.bucket, args.photo, args.model_arn, args.min_confidence
            )
            image.show()

        # stop the model
        stop_model(args.model_arn)
        logger.info(f"Finished stopping model: {args.model_arn}")

    except ClientError as client_err:
        logger.exception(
            "A service client error occurred: "
            + format(client_err.response["Error"]["Message"])
        )

    except ValueError as value_err:
        logger.exception("A value error occurred: " + format(value_err))

    except FileNotFoundError as file_error:
        logger.exception("File not found error: " + format(file_error))

    except Exception as err:
        logger.exception("An error occurred: " + format(err))


if __name__ == "__main__":
    main()
