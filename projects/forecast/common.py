import boto3
import time
from pathlib import Path
import os
import json
import numpy as np

forecast = boto3.client("forecast")
forecastquery = boto3.client(service_name="forecastquery")
s3_client = boto3.client("s3", region_name="us-east-1")


def check_job_status(arn, job_type, auto_ml=False, wait_time=60):
    if job_type == "training":
        job_status = None
        while job_status != "ACTIVE":
            time.sleep(wait_time)
            if auto_ml:
                job_status = forecast.describe_auto_predictor(PredictorArn=arn)[
                    "Status"
                ]
            else:
                job_status = forecast.describe_predictor(PredictorArn=arn)["Status"]
            print(f"Import job still in progress. Job status {job_status}")
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
    elif job_type == "forecast":
        job_status = forecast.describe_forecast(ForecastArn=arn)["Status"]
        while job_status != "ACTIVE":
            print(f"Import job still in progress. Job status {job_status}")
            time.sleep(wait_time)
            job_status = forecast.describe_forecast(ForecastArn=arn)["Status"]

        print(f"Data Import job complete with job status {job_status}")


def read_json(dataset_results_dir, filename):
    json_path = os.path.join(dataset_results_dir, filename)
    with open(json_path, "rb") as f:
        return json.load(f)
