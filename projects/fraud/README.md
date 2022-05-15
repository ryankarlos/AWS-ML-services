### AWS Fraud Detector 

Run the following command specifying the local path to image data to upload and bucket name.
This creates a bucket (if it does not already exists) and then proceeds to the upload step. 

```
$ python s3/transfer_data_s3.py --bucket_name fraud-sample-data --local_dir datasets/fraud
2022-05-15 01:13:13,076 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-05-15 01:13:13,670 __main__ INFO:Bucket 'fraud-sample-data' already exists, so skipping bucket create step
0it [00:00, ?it/s]2022-05-15 01:13:13,688 __main__ INFO:Starting upload ....
0it [00:00, ?it/s]
2022-05-15 01:13:14,118 __main__ INFO:Successfully uploaded all image folders in datasets/fraud to S3  bucket fraud-sample-data
```