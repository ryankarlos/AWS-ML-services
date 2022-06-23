# AWS Fraud Detector 


The datasets `datasets/fraud/dataset1/fraudTest.csv` and `datasets/fraud/dataset1/fraudTrain.csv`  contain  
variables for each online account registration event as required for creating an event 
in AWS Fraud Detector https://docs.aws.amazon.com/frauddetector/latest/ug/create-event-dataset.html: 

This contains the following variables:

index - Unique Identifier for each row
transdatetrans_time - Transaction DateTime
cc_num - Credit Card Number of Customer
merchant - Merchant Name
category - Category of Merchant
amt - Amount of Transaction
first - First Name of Credit Card Holder
last - Last Name of Credit Card Holder
gender - Gender of Credit Card Holder
street - Street Address of Credit Card Holder
city - City of Credit Card Holder
state - State of Credit Card Holder
zip - Zip of Credit Card Holder
lat - Latitude Location of Credit Card Holder
long - Longitude Location of Credit Card Holder
city_pop - Credit Card Holder's City Population
job - Job of Credit Card Holder
dob - Date of Birth of Credit Card Holder
trans_num - Transaction Number
unix_time - UNIX Time of transaction
merch_lat - Latitude Location of Merchant
merch_long - Longitude Location of Merchant
is_fraud - Fraud Flag <--- Target Class

Fraud detector model training requires some mandatory variables in the dataset:

`EVENT_LABEL` A label that classifies the event as 'fraud' or 'legit'.
`EVENT_TIMESTAMP` : The timestamp when the event occurred. The timestamp must be in ISO 8601 standard in UTC.

Using glue we transform the train and test datasets to conform to the AWS Fraud Detector 
requirements



#### CloudFormation Templates


* Detector Rules

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/detector-rules.png"></img>


* Variables

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/variables.png"></img>


### Upload raw data to S3 

Run the following command specifying the local path to fraud test and train raw data to upload 
and bucket name.  This creates a bucket (if it does not already exists) and then 
proceeds to the upload step. 

```
$ python s3/transfer_data_s3.py --bucket_name fraud-sample-data --local_dir datasets/fraud-sample-data/dataset1
2022-05-15 01:21:55,390 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-05-15 01:21:55,982 __main__ INFO:Creating new bucket with name:fraud-sample-data
0it [00:00, ?it/s]2022-05-15 01:21:56,733 __main__ INFO:Starting upload ....
0it [00:00, ?it/s]
2022-05-15 01:21:57,163 __main__ INFO:Successfully uploaded all files in datasets/fraud-sample-data/dataset1 to S3  bucket fraud-sample-data
```

###  Model Training


* Model verison 1
<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/model-v1.png"></img>

* Model version 2

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/modelv2-threshold500.png"></img>


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/modelv2-threshold-305.png"></img>


* Model versions comparison

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/model-versions-performance.png"></img>


### Generate Predictions 


In batch mode

```
python projects/fraud/predictions.py --predictions batch --s3input s3://fraud-sample-data/fraudTest_2020.csv --s3output s3://fraud-sample-data/output_fraudTest_2020.csv --role AmazonFraudDetectorRole
22-06-2022 06:55:51 : INFO : predictions : main : 136 : running batch prediction job
22-06-2022 06:55:57 : INFO : predictions : main : 146 : Job submitted successfully
```

In realtime mode 

```
$ python projects/fraud/predictions.py --predictions realtime --payload_path datasets/fraud-sample-data/dataset1/payload.json --role AmazonFraudDetectorRole
22-06-2022 06:27:36 : INFO : predictions : main : 125 : running realtime prediction

[
    {
        "modelVersion": {
            "modelId": "fraud_model",
            "modelType": "ONLINE_FRAUD_INSIGHTS",
            "modelVersionNumber": "2.0"
        },
        "scores": {
            "fraud_model_insightscore": 56.0
        }
    }
]
```

### Delete S3 bucket

delete selected resources in bucket or entire bucket. If entire bucket not needed to be deleted, then 
`--resource_list` arg can be passed.


```
python s3/cleanup_resources.py --bucket_name=fraud-sample-data
2022-05-15 01:20:00,996 botocore.credentials INFO:Found credentials in shared credentials file: ~/.aws/credentials
2022-05-15 01:20:01,335 __main__ INFO:Deleting all objects in S3 bucket fraud-sample-data as resource key not provided
2022-05-15 01:20:02,707 __main__ INFO:Deleted bucket fraud-sample-data 
```