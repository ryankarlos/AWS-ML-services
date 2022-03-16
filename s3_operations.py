from tqdm import tqdm
import boto3
from pathlib import Path
import botocore
import logging

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s:%(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")


def upload_folder_to_s3(s3_resource, path, bucket_name):
    bucket = s3_resource.Bucket(bucket_name)
    p = Path(path)
    with tqdm(p.glob("**/*.jpeg")) as pbar:
        logger.info("Starting upload ....")
        for child in pbar:
            folder_name = child.parent.name
            if not bucket.objects.filter(Prefix=folder_name):
                bucket.put_object(Key=(folder_name + "/"))
            key = folder_name + "/" + str(child.stem)
            pbar.set_description(
                f"Uploading {str(child)} to folder {folder_name} in S3 bucket {bucket_name}"
            )
            bucket.upload_file(str(child), key)
    logger.info(
        f"Successfully uploaded all image folders in {path} to S3  bucket {bucket.name}"
    )


def create_or_list_buckets(s3_client, bucket_name=None):
    response = s3_client.list_buckets()
    logger.info(f"Existing S3 buckets:{response['Buckets']}")
    if bucket_name is not None:
        if bucket_name in response["Buckets"][0]["Name"]:
            logger.error("Bucket you want to create already exists")
        else:
            logger.info(f"Creating new bucket with name:{bucket_name}")
            s3_client.create_bucket(Bucket=bucket_name)


def delete_s3_bucket_resources(
    s3_client, s3_resource, bucket_name, resource_keys: list, empty_bucket=False
):
    bucket = s3_resource.Bucket(bucket_name)
    if empty_bucket:
        logger.info(f"Deleting S3 bucket {bucket_name}")
        bucket.objects.all().delete()
        return
    else:
        for key in resource_keys:
            logger.info(f"Deleting object {key} in S3 bucket {bucket_name}")
            s3_client.delete_object(bucket_name, Key=key)


def s3_delete_buckets(s3_client, bucket_list):

    for bucket in bucket_list:
        try:
            s3_client.delete_bucket(Bucket=bucket)
            logger.info(f"Deleted bucket {bucket} ")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete s3 bucket {bucket} as it is not empty")


if __name__ == "__main__":
    create_or_list_buckets(s3_client)
    upload_folder_to_s3(s3_resource, "datasets/cv/food101/samples/", "rekognition-cv")
