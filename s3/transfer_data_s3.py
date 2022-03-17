from tqdm import tqdm
import boto3
from pathlib import Path
import logging
import json
import argparse
from bucket_policies import bucket_policy_rekog

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s:%(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")


def create_bucket(s3_client, bucket_name, policy):
    if bucket_name in list_buckets(s3_client)["Buckets"][0]["Name"]:
        logger.error("Bucket you want to create already exists")
    else:
        logger.info(f"Creating new bucket with name:{bucket_name}")
        s3_client.create_bucket(Bucket=bucket_name)
        logger.info(f"Creating bucket policy")
        bucket_policy_str = json.dumps(policy)
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy_str)


def list_buckets(s3_client):
    response = s3_client.list_buckets()
    return response


def upload_folder_to_s3(s3_resource, path, bucket_name):
    bucket = s3_resource.Bucket(bucket_name)
    p = Path(path)
    with tqdm(p.glob("**/*.jpeg")) as pbar:
        logger.info("Starting upload ....")
        project_name = p.stem
        bucket.put_object(Key=(project_name + "/"))
        for child in pbar:
            label_name = child.parent.name
            aws_path = project_name + "/" + label_name
            key = aws_path + "/" + str(child.stem) + ".jpeg"
            pbar.set_description(
                f"Uploading {str(child)} to {aws_path} in S3 bucket {bucket_name}"
            )
            bucket.upload_file(str(child), key)


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument(
        "--bucket_name", help="Name of bucket to create or upload data to"
    )

    parser.add_argument("--local_dir", help="Local image folder path to upload")


def main():
    # get command line arguments
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    add_arguments(parser)
    args = parser.parse_args()
    create_bucket(s3_client, args.bucket_name, policy=bucket_policy_rekog)
    upload_folder_to_s3(s3_resource, args.local_dir, args.bucket_name)
    logger.info(
        f"Successfully uploaded all image folders in {args.local_dir} to S3  bucket {args.bucket_name}"
    )


if __name__ == "__main__":
    main()
