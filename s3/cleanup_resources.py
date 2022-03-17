import boto3
import botocore
import logging
import argparse


logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s:%(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")


def delete_s3_bucket_resources(s3_client, s3_resource, bucket_name, resource_keys=None):
    bucket = s3_resource.Bucket(bucket_name)
    if resource_keys is None:
        logger.info(
            f"Deleting all objects in S3 bucket {bucket_name} as resource key not provided"
        )
        bucket.objects.all().delete()
        return
    else:
        for key in resource_keys:
            logger.info(f"Deleting object {key} in S3 bucket {bucket_name}")
            s3_client.delete_object(bucket_name, Key=key)


def s3_delete_buckets(s3_client, bucket):
    try:
        s3_client.delete_bucket(Bucket=bucket)
        logger.info(f"Deleted bucket {bucket} ")
    except botocore.exceptions.ClientError as e:
        logger.error(f"Cannot delete s3 bucket {bucket} as it is not empty")


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """
    parser.add_argument(
        "--bucket_name", help="Name of bucket name to delete resources from"
    )
    parser.add_argument(
        "--resource_keys",
        help="Name of resource_keys associated with objects to be deleted",
        required=False,
    )


def main():
    # get command line arguments
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    add_arguments(parser)
    args = parser.parse_args()
    delete_s3_bucket_resources(s3_client, s3_resource, args.bucket_name)
    s3_delete_buckets(s3_client, args.bucket_name)


if __name__ == "__main__":
    main()
