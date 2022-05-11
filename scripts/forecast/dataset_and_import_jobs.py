from common import forecast


def create_dataset(dataset_name, freq, schema):
    response = forecast.create_dataset(
        Domain="CUSTOM",
        DatasetType="TARGET_TIME_SERIES",
        DatasetName=dataset_name,
        DataFrequency=freq,
        Schema=schema,
    )

    dataset_arn = response["DatasetArn"]
    print(forecast.describe_dataset(DatasetArn=dataset_arn))
    return dataset_arn


def create_dataset_group_with_dataset(dataset_name, dataset_arn):
    dataset_arns = [dataset_arn]
    try:
        create_dataset_group_response = forecast.create_dataset_group(
            Domain="CUSTOM", DatasetGroupName=dataset_name, DatasetArns=dataset_arns
        )
        dataset_group_arn = create_dataset_group_response["DatasetGroupArn"]
        return dataset_group_arn
    except forecast.exceptions.ResourceAlreadyExistsException:
        print("Dataset group already exists")


def create_import_job(
    bucket_name, key, dataset_arn, role_arn, import_job_name, timestamp_format
):
    ts_s3_data_path = "s3://" + bucket_name + "/" + key
    print(f"S3 URI for your data file = {ts_s3_data_path}")
    ts_dataset_import_job_response = forecast.create_dataset_import_job(
        DatasetImportJobName=import_job_name,
        DatasetArn=dataset_arn,
        DataSource={"S3Config": {"Path": ts_s3_data_path, "RoleArn": role_arn}},
        TimestampFormat=timestamp_format,
    )

    return ts_dataset_import_job_response
