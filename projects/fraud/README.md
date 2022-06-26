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

Cloudformation templates for creating glue development endpoint or the glue and fraud event resources 
are stored in cloudformation folder. The stacks can be created by running the bash script 
below and passing in either 'endpoint' or 'detector' argument to create a glue dve endpoint
stack or frauddetectorglue stack

```
 sh projects/fraud/bash_scripts/create-resources.sh endpoint
Creating glue dev endpoint 

{
    "StackId": "arn:aws:cloudformation:us-east-1:376337229415:stack/GlueEndpointDev/213a61f0-f42e-11ec-b344-0eab2ca9a161"
}

```

The FraudDetectorGlue stack creates the detector and associated rules, the variables, labels and outcomes
for associating with the event type. We can check that these are as they should be from the 
console as in screenshots below.

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

To commence model training, please run the following script. This will instantiate a model 
via the CreateModel operation, which acts as a container for your model versions. If this already exists, then
it will directly progress to the next step which is the CreateModelVersion operation. This starts the training 
process, which results in a specific version of the model. Please refer to the AWS docs for more 
details https://docs.aws.amazon.com/frauddetector/latest/ug/building-a-model.html

The script fetches the variables for the training job from S3 path which contains the csv file 
with the training data. 

```
$ python projects/fraud/training.py
Starting model training with variables ['cc_num', 'merchant', 'category', 'amt', 'first', 'last', 'gender', 'street', 'city', 'state', 'zip', 'city_pop', 'job', 'trans_num']....
{'modelId': 'fraud_model', 'modelType': 'ONLINE_FRAUD_INSIGHTS', 'modelVersionNumber': '1.0', 'status': 'TRAINING_IN_PROGRESS', 'ResponseMetadata': {'RequestId': 'a1fac915-282d-4dc6-93a5-4331e579f64a', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Sat, 25 Jun 2022 03:18:01 GMT', 'content-type': 'application/x-amz-json-1.1', 'content-length': '120', 'connection': 'keep-alive', 'x-amzn-requestid': 'a1fac915-282d-4dc6-93a5-4331e579f64a'}, 'RetryAttempts': 0}}
```


i have found that if the event metadata columns e.g. EVENT_TIMESTAMP and EVENT_LABEL
are not ordered together in the csv file then you get the following exception when
trying to run the training script to create a model version. This exception went away 
after I ordered the columns so that all the event variables were at the start and the 
last two columns were event metadata i.e. EVENT_TIMESTAMP, EVENT_LABEL

```
$  python projects/fraud/training.py
Traceback (most recent call last):
  File "/Users/rk1103/Documents/AWS-ML-services/projects/fraud/training.py", line 60, in <module>
    train_fraud_model()
  File "/Users/rk1103/Documents/AWS-ML-services/projects/fraud/training.py", line 44, in train_fraud_model
    fraudDetector.create_model_version(
  File "/Users/rk1103/.local/share/virtualenvs/AWS-ML-services-sGYPpasX/lib/python3.9/site-packages/botocore/client.py", line 508, in _api_call
    return self._make_api_call(operation_name, kwargs)
  File "/Users/rk1103/.local/share/virtualenvs/AWS-ML-services-sGYPpasX/lib/python3.9/site-packages/botocore/client.py", line 915, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.errorfactory.ResourceNotFoundException: An error occurred (ResourceNotFoundException) when calling the CreateModelVersion operation: VariableIds: [EVENT_TIMESTAMP] do not exist.
```

If model training already in progress, and you run the python script, you will get the 
following validation exception 

```
$  python projects/fraud/training.py

Starting model training with variables ['cc_num', 'merchant', 'category', 'amt', 'first', 'last', 'gender', 'street', 'city', 'state', 'zip', 'city_pop', 'job', 'trans_num']....
An error occurred (ValidationException) when calling the CreateModelVersion operation: Simultaneous training for the same major version not allowed.
Traceback (most recent call last):
  File "/Users/rk1103/Documents/AWS-ML-services/projects/fraud/training.py", line 69, in <module>
    train_fraud_model()
  File "/Users/rk1103/Documents/AWS-ML-services/projects/fraud/training.py", line 47, in train_fraud_model
    fraudDetector.create_model_version(
  File "/Users/rk1103/.local/share/virtualenvs/AWS-ML-services-sGYPpasX/lib/python3.9/site-packages/botocore/client.py", line 508, in _api_call
    return self._make_api_call(operation_name, kwargs)
  File "/Users/rk1103/.local/share/virtualenvs/AWS-ML-services-sGYPpasX/lib/python3.9/site-packages/botocore/client.py", line 915, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.errorfactory.ValidationException: An error occurred (ValidationException) when calling the CreateModelVersion operation: Simultaneous training for the same major version not allowed
```

* Model verison 1
<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/model-v1.png"></img>

* Model version 2

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/modelv2-threshold500.png"></img>


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/modelv2-threshold-305.png"></img>


* Model versions comparison

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/model-versions-performance.png"></img>


### Deploying model


```
$ python projects/fraud/deploy.py --update_rule 1 --model_version 1.0 --rules_version 2                
26-06-2022 04:50:34 : INFO : deploy : main : 121 : Updating rule version 1
26-06-2022 04:50:34 : INFO : deploy : update_detector_rules : 71 : Updating Investigate rule ....
{'detectorId': 'fraud_detector_demo', 'ruleId': 'investigate', 'ruleVersion': '2'}

26-06-2022 04:50:35 : INFO : deploy : update_detector_rules : 80 : Updating review rule ....
{'detectorId': 'fraud_detector_demo', 'ruleId': 'review', 'ruleVersion': '2'}

26-06-2022 04:50:35 : INFO : deploy : update_detector_rules : 89 : Updating approve rule ....
{'detectorId': 'fraud_detector_demo', 'ruleId': 'approve', 'ruleVersion': '2'}

26-06-2022 04:50:35 : INFO : deploy : main : 123 : Deploying trained model version 1.0 to new detector version 
{'detectorId': 'fraud_detector_demo', 'detectorVersionId': '2', 'status': 'DRAFT', 'ResponseMetadata': {'RequestId': 'da37d973-2c43-4c56-93e5-f9b9bd132bb3', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Sun, 26 Jun 2022 03:50:36 GMT', 'content-type': 'application/x-amz-json-1.1', 'content-length': '77', 'connection': 'keep-alive', 'x-amzn-requestid': 'da37d973-2c43-4c56-93e5-f9b9bd132bb3'}, 'RetryAttempts': 0}}

```

### Generate Predictions 


In batch mode

```
python projects/fraud/predictions.py --predictions batch --detector_version 2 --s3input s3://fraud-sample-data/fraudTest_2020.csv --s3output s3://fraud-sample-data/output_fraudTest_2020.csv --role AmazonFraudDetectorRole
22-06-2022 06:55:51 : INFO : predictions : main : 136 : running batch prediction job
22-06-2022 06:55:57 : INFO : predictions : main : 146 : Job submitted successfully
```

In realtime mode 

```

$ (AWS-ML-services) (base) rk1103@Ryans-MacBook-Air AWS-ML-services % python projects/fraud/predictions.py \
--predictions realtime --payload_path datasets/fraud-sample-data/dataset1/payload.json --detector_version 2 \
--role AmazonFraudDetectorRole
26-06-2022 04:13:54 : INFO : predictions : main : 152 : running realtime prediction

[
    {
        "modelVersion": {
            "modelId": "fraud_model",
            "modelType": "ONLINE_FRAUD_INSIGHTS",
            "modelVersionNumber": "1.0"
        },
        "scores": {
            "fraud_model_insightscore": 24.0
        }
    }
]
```

###Teardown resources 

Run the bash script passing in the 'endpoint' or 'detector' command depending on 
which resources you want to delete 

For the endpoint resource:

```
sh projects/fraud/bash_scripts/teardown.sh endpoint
echo "Deleting endpoint"

```
For tearing down the trained fraud model, detector (including rules), event type 
(including outcomes, variables, labels), run the following:

```
sh projects/fraud/bash_scripts/teardown.sh

Delete model versions

Delete model

Deleting detector version id 1

Deleting rule investigate
Deleting rule review
Deleting rule approve

Deleting detector id fraud_detector_demo

Deleting event-type credit_card_transaction

Deleting entity-type customer

Deleting variable trans_num
Deleting variable amt
Deleting variable city_pop
Deleting variable street
Deleting variable job
Deleting variable cc_num
Deleting variable gender
Deleting variable merchant
Deleting variable last
Deleting variable category
Deleting variable zip
Deleting variable city
Deleting variable state
Deleting variable first

Deleting label legit
Deleting label fraud

Deleting outcome high_risk
Deleting outcome low_risk
Deleting outcome medium_risk

Deleting cloud formation stack

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