# AWS Fraud Detector 

This example will follow the AWS tutorial on Fraud Detector https://docs.aws.amazon.com/frauddetector/latest/ug/part-a.html
However, we will implement it directly with step functions. The sample data is in 
`datasets/fraud/registration_data_20K_minimum.csv` and can be downloaded from 
https://docs.aws.amazon.com/frauddetector/latest/ug/step-1-get-s3-data.html.
The dataset contains  variables for each online account registration event as required 
for creating an event in AWS Fraud Detector https://docs.aws.amazon.com/frauddetector/latest/ug/create-event-dataset.html: 

Event variables:(`ip_address`,`email_address`,`user_agent`,`phone_number`,`billing_address`)
Event metadata (should be upper case column names in dataset as described in 
https://docs.aws.amazon.com/frauddetector/latest/ug/create-event-dataset.html): 

`EVENT_LABEL` A label that classifies the event as 'fraud' or 'legit'.
`EVENT_TIMESTAMP` : The timestamp when the event occurred. The timestamp must be in ISO 8601 standard in UTC.

### Upload data to S3 

Run the following command specifying the local path to image data to upload and bucket name.
This creates a bucket (if it does not already exists) and then proceeds to the upload step. 

```
$ python s3/transfer_data_s3.py --bucket_name fraud-sample-data --local_dir datasets/fraud
2022-05-15 01:21:55,390 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-05-15 01:21:55,982 __main__ INFO:Creating new bucket with name:fraud-sample-data
0it [00:00, ?it/s]2022-05-15 01:21:56,733 __main__ INFO:Starting upload ....
0it [00:00, ?it/s]
2022-05-15 01:21:57,163 __main__ INFO:Successfully uploaded all image folders in datasets/fraud to S3  bucket fraud-sample-data
```


### Delete bucket

elete selected resources in bucket or entire bucket. If entire bucket not needed to be deleted, then 
`--resource_list` arg can be passed.


```
python s3/cleanup_resources.py --bucket_name=fraud-sample-data
2022-05-15 01:20:00,996 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-05-15 01:20:01,335 __main__ INFO:Deleting all objects in S3 bucket fraud-sample-data as resource key not provided
2022-05-15 01:20:02,707 __main__ INFO:Deleted bucket fraud-sample-data 
```