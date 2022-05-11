import boto3
import time


forecast = boto3.client("forecast")
forecastquery = boto3.client(service_name="forecastquery")
s3_client = boto3.client("s3", region_name="us-east-1")

def check_job_status(arn, job_type, wait_time=60):
    if job_type == "training":
        job_status = forecast.describe_predictor(PredictorArn=arn)["Status"]
        while job_status != "ACTIVE":
            print(f"Import job still in progress. Job status {job_status}")
            time.sleep(wait_time)
            job_status = forecast.describe_predictor(PredictorArn=arn)["Status"]
        print(f"Training job complete with job status {job_status}")
    elif job_type == "import_data":
        job_status = forecast.describe_dataset_import_job(DatasetImportJobArn=arn)[
            "Status"
        ]
        while job_status != "ACTIVE":
            print(f"Import job still in progress. Job status {job_status}")
            time.sleep(wait_time)
            job_status = forecast.describe_dataset_import_job(DatasetImportJobArn=arn)[
                "Status"
            ]
        print(f"Data Import job complete with job status {job_status}")
