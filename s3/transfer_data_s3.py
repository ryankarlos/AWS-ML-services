from pathlib import Path
import json
import argparse
import logging
import boto3
from botocore.exceptions import ClientError
import os

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s:%(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")


def create_bucket(s3_client, bucket_name, policy_path=None):
    response = s3_client.list_buckets()["Buckets"]
    bucket_list = [bucket["Name"] for bucket in response]
    if bucket_name in bucket_list:
        logger.info(
            f"Bucket '{bucket_name}' already exists, so skipping bucket create step"
        )
    else:
        logger.info(f"Creating new bucket with name:{bucket_name}")
        s3_client.create_bucket(Bucket=bucket_name)
        if policy_path is not None:
            with open(policy_path, "rb") as f:
                policy = json.load(f)
            logger.info(f"Creating bucket policy")
            bucket_policy_str = json.dumps(policy)
            s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy_str)


def upload_files(path, bucket):
    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            object_name = os.path.relpath(full_path, path)
            try:
                s3_client.upload_file(full_path, bucket, object_name)
            except ClientError as e:
                logging.error(e)
                return False


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument(
        "--bucket_name", help="Name of bucket to create or upload data to"
    )

    parser.add_argument("--local_dir", help="Local folder path to upload")
    parser.add_argument("--policy_filename", help="filename of resource policy")


def main():
    # get command line arguments
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    add_arguments(parser)
    args = parser.parse_args()
    policy_filename = args.policy_filename
    if policy_filename is not None:
        policy_path = os.path.join(
            str(Path(__file__).parent), "resource_policies", policy_filename
        )
        create_bucket(s3_client, args.bucket_name, policy_path=policy_path)
    else:
        create_bucket(s3_client, args.bucket_name)
    dataset_path = os.path.join(str(Path(__file__).parents[1]), args.local_dir)
    upload_files(dataset_path, args.bucket_name)
    logger.info(
        f"Successfully uploaded all files in {args.local_dir} to S3  bucket {args.bucket_name}"
    )


if __name__ == "__main__":
    main()
