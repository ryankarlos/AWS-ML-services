
Output of transfer data script, creates or lists existing buckets and loads image data from local folders to S3

```
$ python s3/transfer_data_s3.py --bucket_name=rekognition-cv --local_dir='datasets/cv/food101/food101_aws'

2022-03-17 02:01:06,771 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-03-17 02:01:07,418 __main__ INFO:Creating new bucket with name:rekognition-cv
2022-03-17 02:01:08,103 __main__ INFO:Creating bucket policy
0it [00:00, ?it/s]2022-03-17 02:01:08,303 __main__ INFO:Starting upload ....
Uploading datasets\cv\food101\food101_aws\pizza\99811.jpeg to food101_aws/pizza in S3 bucket rekognition-cv: : 1000it [04:56,  3.38it/s]
2022-03-17 02:06:04,436 __main__ INFO:Successfully uploaded all image folders in datasets/cv/food101/food101_aws to S3  bucket rekognition-cv

```

Cleanup script to remove entire bucket - first deletes all resources and then deletes bucket.
If entire bucket not needed to be deleted, then resource_list arg can be passed.

```
$ python s3/cleanup_resources.py --bucket_name=rekognition-cv

2022-03-17 01:15:41,602 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-03-17 01:15:41,787 __main__ INFO:Deleting all objects in S3 bucket rekognition-cv as resource key not provided
2022-03-17 01:15:46,606 __main__ INFO:Deleted bucket rekognition-cv
```