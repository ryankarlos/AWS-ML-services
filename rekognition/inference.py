import random
import boto3
import logging
import argparse
from botocore.exceptions import ClientError
import io
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import ast


rek_client = boto3.client("rekognition")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def start_model(project_arn, model_arn, min_inference_units):
    client = boto3.client("rekognition")

    try:
        # Start the model
        response = client.start_project_version(
            ProjectVersionArn=model_arn, MinInferenceUnits=min_inference_units
        )
        p = Path(model_arn)
        version_name = p.parts[-2]
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
            logger.info("Status: " + model["Status"])
            logger.info("Message: " + model["StatusMessage"])
    except Exception as e:
        print(e)

    print("Done...")


def stop_model(model_arn):

    client = boto3.client("rekognition")

    logging.info("Stopping model:")

    # Stop the model
    try:
        response = client.stop_project_version(ProjectVersionArn=model_arn)
        status = response["Status"]
        print("Status: " + status)
    except Exception as e:
        print(e)


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


def get_random_img_for_label_detection(path, labels_list):
    p = Path(path)
    # list all the subfolders (food label names)
    label_paths = [x for x in p.glob("*") if x.stem in labels_list]
    subfolder_path = random.choice(label_paths)
    # list all the images
    image_list = list(subfolder_path.glob("*.jpg"))
    image_path = random.choice(image_list)
    correct_label = image_path.parent.stem
    return image_path, correct_label


def add_arguments():
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """
    # get command line arguments
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    parser.add_argument(
        "--model_arn",
        help="The ARN of the model that you want to use.",
    )
    parser.add_argument(
        "--project_arn",
        help="The ARN of the project that contains that the model you want to start.",
    )
    parser.add_argument(
        "--image",
        help="The path to the image folders to randomly sample images to be analysed",
    )
    parser.add_argument(
        "--labels_list",
        default='["apple_pie", "chocolate_cake", "fish_and_chips", "pizza"]',
        type=ast.literal_eval,
        help="Expected labels for checking accuracy of algorithm",
    )
    parser.add_argument(
        "--min_inference_units",
        default=1,
        help="The minimum number of inference units to use.",
    )
    parser.add_argument(
        "--min_confidence",
        default=60,
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

    args = parser.parse_args()

    return args


def main():
    try:
        args = add_arguments()

        # start the model
        logger.info(f"Starting model")
        start_model(
            args.project_arn,
            args.model_arn,
            args.min_inference_units,
        )
        logger.info(f"Finished starting model")

        # Analyze image

        if args.bucket is None:
            logger.info(
                f"Analysing random 10 samples of local images as --bucket arg not supplied"
            )
            num_images_to_detect = 10
            correct_detection_counter  = 0
            low_confidence_counter = 0
            for _ in range(num_images_to_detect):
                image_path, correct_label = get_random_img_for_label_detection(
                    args.image, args.labels_list
                )
                response, image = analyze_local_image(
                    rek_client, args.model_arn, image_path, args.min_confidence
                )
                image.show()
                if not response['CustomLabels']:
                    low_confidence_counter += 1
                else:
                    if response['CustomLabels'][0]["Name"] == correct_label:
                        correct_detection_counter += 1
            logger.info(f'Model detected {correct_detection_counter} out of {num_images_to_detect} correctly')
            logger.info(f'Model could not detect {low_confidence_counter} images due to confidence below threshold {args.min_confidence}')
        else:
            if args.photo is None:
                raise ValueError(
                    f"--photo arg also needs to be supplied if fetching image from s3 bucket"
                )
            response, image = analyze_s3_image(
                rek_client, args.bucket, args.photo, args.model_arn, args.min_confidence
            )

            image.show()

        # stop the model
        stop_model(args.model_arn)
        logger.info(f"Finished stopping model")

    except ClientError as client_err:
        logger.exception(
            "A service client error occurred: "
            + format(client_err.response["Error"]["Message"])
        )

    except ValueError as value_err:
        logger.exception("A validation error occurred: " + format(value_err))

    except ValueError as value_err:
        logger.exception("A value error occurred: " + format(value_err))

    except FileNotFoundError as file_error:
        logger.exception("File not found error: " + format(file_error))

    except Exception as err:
        logger.exception("An error occurred: " + format(err))


if __name__ == "__main__":
    main()
