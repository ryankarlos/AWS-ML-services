
Output of transfer data script, creates or lists existing buckets and loads image data from local folders to S3

```
$ python s3/transfer_data_s3.py --bucket_name=rekognition-cv --local_dir='datasets/cv/food101/food101_aws'

2022-03-16 21:05:13,631 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-03-16 21:05:14,372 __main__ INFO:Existing S3 buckets:[{'Name': 'rekognition-cv', 'CreationDate': datetime.datetime(2022, 3, 16, 2, 40, 23, tzinfo=tzutc())}]
0it [00:00, ?it/s]2022-03-16 21:05:14,372 __main__ INFO:Starting upload ....
Uploading datasets\cv\food101\samples\pizza\99811.jpeg to folder pizza in S3 bucket rekognition-cv: : 1000it [05:18,  3.14it/s]
2022-03-16 21:10:32,763 __main__ INFO:Successfully uploaded all image folders in datasets/cv/food101/samples/ to S3  bucket rekognition-cv
```

Cleanup script to remove entire bucket - first deletes all resources and then deletes bucket.
If entire bucket not needed to be deleted, then resource_list arg can be passed.

```
$ python s3/cleanup_resources.py --bucket_name=rekognition-cv

2022-03-17 01:15:41,602 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-03-17 01:15:41,787 __main__ INFO:Deleting all objects in S3 bucket rekognition-cv as resource key not provided
2022-03-17 01:15:46,606 __main__ INFO:Deleted bucket rekognition-cv
```