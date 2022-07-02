# AWS Fraud Detector 

Amazon Fraud Detector is a fully managed service that can identify potentially fraudulent online activities. 
These can be situations such as the creation of fake accounts or online payment fraud. 
Amazon Fraud Detector automates the time-consuming and expensive steps to build, train, and deploy an ML model for fraud 
detection. It customizes each model it creates to your dataset, making the accuracy of models higher 
than current one-size-fits-all ML solutions. And because you pay only for what you use, you can avoid large upfront expenses.
The example below, uses simulated train and test datasets from Kaggle and can be downloaded from 
https://www.kaggle.com/datasets/kartik2112/fraud-detection
The datasets `fraudTest.csv` and `fraudTrain.csv`  contain variables for each online account registration event as required for creating an event 
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


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/fraud_train_architecture.png"></img>


The architecture for model training has been generated using the diagrams package via script in screenshots\aws_diagrams\fraud_train.py
These resources are already created and configured via the cloudformation stack. A Glue crawler run by the user crawls the train and test csv 
files in the S3 bucket and creates a combined table with all the data. We have configured S3 to send notifications to SQS 

This will instantiate a model  via the CreateModel operation, which acts as a container for your model versions. If this already exists, then
it will directly progress to the next step which is the CreateModelVersion operation. This starts the training 
process, which results in a specific version of the model. Please refer to the AWS docs for more 
details https://docs.aws.amazon.com/frauddetector/latest/ug/building-a-model.html
The script fetches the variables for the training job from S3 path which contains the csv file 
with the training data. 

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/train-model-lambda-logs.png"></img>

i have found that if the event metadata columns e.g. EVENT_TIMESTAMP and EVENT_LABEL
are not ordered together in the csv file then you get the following exception. This exception went away 
after I ordered the columns so that all the event variables were at the start and the 
last two columns were event metadata i.e. EVENT_TIMESTAMP, EVENT_LABEL

```
botocore.errorfactory.ResourceNotFoundException: An error occurred (ResourceNotFoundException) when calling the CreateModelVersion operation: VariableIds: [EVENT_TIMESTAMP] do not exist.
```

If model training already in progress, and you run the python script to update the same model version, the logs should
print out a message saying 'Model Version already training' and will exit.

To start model training in local mode, run the following script stored in `projects/fraud/training.py`. This calls the FraudDetector 
api directly after dong the necessary data processing from data in S3 (i.e. it avoids the use of Glue Crawler and Glue used in the architecture above). 
This is useful for quick troubleshooting.

```
$ python projects/fraud/training.py
Starting model training with variables ['cc_num', 'merchant', 'category', 'amt', 'first', 'last', 'gender', 'street', 'city', 'state', 'zip', 'city_pop', 'job', 'trans_num']....
{'modelId': 'fraud_model', 'modelType': 'ONLINE_FRAUD_INSIGHTS', 'modelVersionNumber': '1.0', 'status': 'TRAINING_IN_PROGRESS', 'ResponseMetadata': {'RequestId': 'a1fac915-282d-4dc6-93a5-4331e579f64a', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Sat, 25 Jun 2022 03:18:01 GMT', 'content-type': 'application/x-amz-json-1.1', 'content-length': '120', 'connection': 'keep-alive', 'x-amzn-requestid': 'a1fac915-282d-4dc6-93a5-4331e579f64a'}, 'RetryAttempts': 0}}
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

* Model version 1
<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/model-v1.png"></img>

* Model version 2

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/modelv2-threshold500.png"></img>


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/modelv2-threshold-305.png"></img>


* Model versions comparison

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/model-versions-performance.png"></img>


### Deploying model


If we are happy with the model trained, we need to make it active by deploying it
Scroll to the top of the Version details page and choose Actions, Deploy model version. On the Deploy model version p
prompt that appears, choose Deploy version.
The Version details shows a Status of Deploying. When the model is ready, the Status changes to Active.
Once model has finished deploying and status changed to active, we will need to associate the model with Fraud Detector 
for predictions.
However, we will also need to update the rule expressions as the default Fraud Detector version 1 created from cloudformation 
uses the variable 'amt' in the rule expression. We need to change this to model insight score which is a new variable created 
after model training has completed. This variable is not available when the cloudformation stack is created as the model has not been 
trained yet so we needed to have a placeholder existing variable so the rule expression is valid
to avoid the stack for throwing an error

We can run the following script to update the detector rules and associate the new model with it. This will carry out two steps.

Firstly, it will update the existing rule version with the correct expression based on the number passed to the --update_rule argument. It will create 
a new rule version (incremented from the original, eg 2 if the original is 1). Then it will create a new detector version 
and associate the model version (--model_version arg) and the rules_version (--rules_version arg) which should be set to be 
the increment of the existing rule version.
This will automatically increment the detector version to 2.0 as the existing version is 1.0

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

The screenshots below show the model associated with the new version and the correct rules expressions which use the
`fraud_model_insightscore` variable


#### Setting up API gateway 

1. Open the API Gateway console, and then choose your API.
2. Select CreateAPI and select the type as RestAPI
3. Protocol: REST, Create New API and choose a name and optional description
4. Select the API resource just created and select Create Method from the Resource Actions. Select Get
5. In the Get-Setup, select Integration Type: lambda function and lambda function name 'PredictFraudModel'. Click save.
6. In the Method Execution pane, choose Method Request.
7. In settings, set Request Validator: 'Validate query string parameters and headers'. Leave Authorization as 'None'.
8. Expand the URL Query String Parameters dropdown, then choose Add query string.
9. Enter the following variables one by one as a separate name field. Mark all as required except for 'flow_definition' variable

```
 amt, category, cc_num, city, city_pop, event_timestamp, first, flow_definition, gender, job, last, merchant, state, street, trans_num, zip
```

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/API-gateway-method-request-console.png"></img>

10 Go back to the Method Execution pane.It should look like below.

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/API-gateway-method-execution-console.png"></img>

11. Choose Integration Request.
12. Choose the Mapping Templates dropdown and then choose Add mapping template.
13. For the Content-Type field, enter application/json and then choose the check mark icon.
14. In the pop-up that appears, choose Yes, secure this integration.
15. For Request body passthrough, choose When there are no templates defined (recommended).
16. In the mapping template editor, copy and replace the existing script with the following code:

```
#if("$input.params('flow_definition')" != "")
#set( $my_default_value = "$input.params('flow_definition')")
#else
#set ($my_default_value = "ignore")
#end


{
  "variables": {
        "trans_num":"$input.params('trans_num')",
        "amt":"$input.params('amt')",
        "zip":"$input.params('zip')",
        "city":"$input.params('city')",
        "first":"$input.params('first')",
        "job":"$input.params('job')",
        "street":"$input.params('street')",
        "category":"$input.params('category')",
        "city_pop":"$input.params('city_pop')",
        "gender":"$input.params('gender')",
        "cc_num":"$input.params('cc_num')",
        "last":"$input.params('last')",
        "state":"$input.params('state')",
        "merchant":"$input.params('merchant')"
  },
  "EVENT_TIMESTAMP":"$input.params('event_timestamp')",
  "flow_definition":"$my_default_value"
}
```

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/API-gateway-integration-request-console.png"></img>

17. Choose Save, and go back to MethodExecution pane. Click on Test button on the left.
18. In the Query Strings box paste the following

```
trans_num=6cee353a9d618adfbb12ecad9d427244&amt=245.97&zip=97383&city=Stayton&first=Erica&job=Engineer, biomedical&street=213 Girll Expressway&category=shopping_pos&city_pop=116001&gender=F&cc_num=180046165512893&last=Walker&state=OR&merchant=fraud_Macejkovic-Lesch&event_timestamp=2020-10-13T09:21:53.000Z&flow_definition=arn:aws:sagemaker:us-east-1:376337229415:flow-definition/fraud-detector-a2i-1656277295743
```

If successful you should see the response and logs as in screenshot below. You can also navigate to CloudWatch log stream group for Lambda invocation and check it has run successfully.

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/API-gateway-get-method-test1-console.png"></img>

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/API-gateway-get-method-test2logs-console.png"></img>

We can then proceed to deploying the API. Go back to Resources -> Actions and Deploy API. Select Deployment Stage 'New Stage' and choose name as 'dev'.
You should see the API endpoint to invoke on the console.

Finally make sure logging is setup to allow debugging errors in  the REST API, ny following the instructions here
https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-cloudwatch-logs/

The setup should look like below. Note that when you add the iam role to gateway console, it should automatically add the log group 
in the format 'API-Gateway-Execution-Logs_apiId/stageName'. The arn for the log group end with 'dev:*'. You need to only include the 
arn upto the stagename 'dev' as shown in the screenshot below - otherwise it will throw issues with the validation checks.

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/api-rest-stage-editor-logs-config.png"></img>


To test the API's new endpoint, run the following curl command. Make sure that the curl command has the query string parameters at the end as below ('key=value' format and separated by &).
Since the get method is configured in '/' root resource - we can invoke the api endpoint https://d9d16i7hbc.execute-api.us-east-1.amazonaws.com/dev

```
curl -X GET https://d9d16i7hbc.execute-api.us-east-1.amazonaws.com/dev?trans_num=6cee353a9d618adfbb12ecad9d427244&amt=245.97&zip=97383&city=Stayton&first=Erica&job='Engineer, biomedical'&street='213 Girll Expressway'&category=shopping_pos&city_pop=116001&gender=F&cc_num=180046165512893&last=Walker&state=OR&merchant=fraud_Macejkovic-Lesch&event_timestamp=2020-10-13T09:21:53.000Z
```

You can check the log streams associated with the latest invocation in the cloudwatch log group for API gateway. This will show  messages 
with the execution or access details of your request.

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/API-gateway-cloudwatch-log-group.png"></img>

Note: If any changes are made to the api configuration or parameters - it would need to be redployed for the changes to take effect.

### Generate Predictions 


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/Fraud_prediction_architecture.png"></img>


The architecture diagram above shows the two modes we can use for making predictions with Amazon Fraud Detector: batch and real-time.

You can use a batch predictions job in Amazon Fraud Detector to get predictions for a set of events that do not require real-time scoring. 
You may want to generate fraud predictions for a batch of events. These might be payment fraud, 
account take over or compromise, and free tier misuse while performing an offline proof-of-concept. 
You can also use batch predictions to evaluate the risk of events on an hourly, daily, or weekly basis depending upon your business need.
If you want to analyze fraud transactions after the fact, you can perform batch fraud predictions using Amazon Fraud Detector. 
Then you can store fraud prediction results in an Amazon S3 bucket. 
Although beyond the scope of this example, we could have also used additional services like Amazon Athena  to help analyze 
the fraud prediction results (once delivered in S3) and Amazon QuickSight for visualising the results on a dashboard.
Copy the batch sample file delivered in the  glue_transformed folder (following successful glue job run) to batch_predict folder.
This will trigger notification to SQS queue which has Lambda function as target, which starts the batch prediction job in Fraud Detector

```
$ aws s3 cp s3://fraud-sample-data/glue_transformed/test/fraudTest.csv s3://fraud-sample-data/batch_predict/fraudTest.csv
copy: s3://fraud-sample-data/glue_transformed/test/fraudTest.csv to s3://fraud-sample-data/batch_predict/fraudTest.csv
```

we can monitor the batch prediction jobs in Fraud Detector. Once complete,we should see the output in S3. An example of 
a batch output is available in datasets/dataset1/results/DetectorBatchResult.csv


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/batch_prediction_jobs.png"></img>


In realtime mode, we will make use of the API gateway created and integrated with the lambda function which makes the 
'get_event_prediction' api call to FraudDetector. 
In this example we are using the same lambda for batch and realtime predictions. The code in lamdba checks the  
checks the event payload to see if certain keys are present which are expected from a request from API gateway (.i.e after the request 
is transformed via the mapping template in api gateway). We have configured the mapping template to create a variables key, so 
we can check if the payload has 'variables' key,  to run realtime prediction. If the event payload has 'Records' key, 
it indicates the event is coming from  SQS and will run a batch prediction job. 
Ideally, I could have had separate lambda for realtime and batch prediction to make it easier to manage. 

To run realtime prediction, API gateway REST API has been configured to accept query string parameters and send the request to lambda
as explained in the previous section. This could be invoked by the following command 

```
curl -X GET https://d9d16i7hbc.execute-api.us-east-1.amazonaws.com/dev?trans_num=6cee353a9d618adfbb12ecad9d427244&amt=245.97&zip=97383&city=Stayton&first=Erica&job='Engineer, biomedical'&street='213 Girll Expressway'&category=shopping_pos&city_pop=116001&gender=F&cc_num=180046165512893&last=Walker&state=OR&merchant=fraud_Macejkovic-Lesch&event_timestamp=2020-10-13T09:21:53.000Z
```

To run batch and realtime prediction modes from local machine (for troubleshooting purposes) to call AWS Fraud Detector API directly, we can use the script in the `projects/fraud/predictions.py`
are adapted compared to the code in lambda (for realtime mode). This uses custom cli arguments to pass the path to payload path (for realtime mode),  
and the method of execution ('realtime' or batch) via the 'prediction' arg

* In batch mode

```
$ python projects/fraud/predictions.py --predictions batch --detector_version 2 --s3input s3://fraud-sample-data/glue_transformed/test/fraudTest.csv --s3output s3://fraud-sample-data/DetectorBatchResults.csv --role FraudDetectorRoleS3Access
27-06-2022 02:35:38 : INFO : predictions : main : 149 : running batch prediction job
27-06-2022 02:35:45 : INFO : predictions : main : 163 : Batch Job submitted successfully
{'batchPredictions': [{'jobId': 'credit_card_transaction-1656293738', 'status': 'IN_PROGRESS_INITIALIZING', 'startTime': '2022-06-27T01:35:39Z', 'lastHeartbeatTime': '2022-06-27T01:35:39Z', 'inputPath': 's3://fraud-sample-data/glue_transformed/test/fraudTest.csv', 'outputPath': 's3://fraud-sample-data/DetectorBatchResults.csv', 'eventTypeName': 'credit_card_transaction', 'detectorName': 'fraud_detector_demo', 'detectorVersion': '2', 'iamRoleArn': 'arn:aws:iam::376337229415:role/FraudDetectorRoleS3Access', 'arn': 'arn:aws:frauddetector:us-east-1:376337229415:batch-prediction/credit_card_transaction-1656293738', 'processedRecordsCount': 0}], 'ResponseMetadata': {'RequestId': 'af585d00-23f0-4a05-82dc-712057c9f912', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Mon, 27 Jun 2022 01:35:44 GMT', 'content-type': 'application/x-amz-json-1.1', 'content-length': '623', 'connection': 'keep-alive', 'x-amzn-requestid': 'af585d00-23f0-4a05-82dc-712057c9f912'}, 'RetryAttempts': 0}}

```

* In realtime mode 

```

$ (AWS-ML-services) (base) rk1103@Ryans-MacBook-Air AWS-ML-services % python projects/fraud/predictions.py \
--predictions realtime --payload_path datasets/fraud-sample-data/dataset1/payload.json --detector_version 2 \
--role AmazonFraudDetectorRole
26-06-2022 04:13:54 : INFO : predictions : main : 152 : running realtime prediction

[
    {
        "modelVersion": {, 
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


#### Augmented AI for reviews 

First need to create a user pool via AWS Cognito, and add yourself as user in the user group, so you can sign into the ]
app using AWS Cognito
https://docs.aws.amazon.com/cognito/latest/developerguide/tutorial-create-user-pool.html.
Once you add yourself as a user (with email address), you will get an email notification  with temporary credentials to log in
and verify email address listed. 
Then we can create a private workforce and a private team associated with the user pool just created. Within a given private
workforce, once can create multiple private teams, where a single private team is assigned the job of completing a 
given human review or labelling task e.g. labelling medical images. By creating and managing 
the private workforce using Amazon Cognito you avoid the overhead of managing worker credentials and authentication, as AWS Cognito, 
provides authentication, authorization, and user management for the users in the workforce.
Following these instructions under 'Create an Amazon Cognito Workforce Using the Labeling Workforces Page' section to
create a private workforce in Sagemaker console which uses AWS Cognito as an identity provider 
https://docs.aws.amazon.com/sagemaker/latest/dg/sms-workforce-create-private-console.html#create-workforce-sm-console. 

After you import your private workforce, refresh the page to see the Private workforce summary page as in screenshot below.

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screnshots/fraud/sagemaker-workforces-console.png"></img>

On this page, you can see information about the Amazon Cognito user pool for your workforce,  the worker team name 'AugmentedAI-Default' 
for your workforce, and a list of all the members of your private workforce. 
This workforce is now available to use in both Amazon Augmented AI and Amazon SageMaker Ground Truth for 
human review tasks and data labeling jobs respectively.
If you click on the private team name 'AugmentedAI-Default' , you should see the Cognito user group linked to it

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/sagemaker-workforce-team.png"></img>

Once the workforce is created, we can run the script below passing in the workforce arn as an arg to create 
a human task UI using a custom worker template defined in `augmented_ai\fraud\constants.py`. Amazon A2I uses this 
to generate the worker task UI, after passing it as argument to SageMaker API operation CreateHumanTaskUi. 
For instructions on creating a custom template, see Create Custom Worker Task Template.
https://docs.aws.amazon.com/sagemaker/latest/dg/a2i-custom-templates.html
The script also uses the `Create Flow Definition` API to create a workflow definition. 

```
$ export PYTHONPATH=.
$ python augmented_ai/fraud/create_workflow.py --workteam_arn <workforce-arn>
Created human task ui with Arn: .......human-task-ui/fraud9079296d-f592-11ec-92fc-50ebf6424219
Created flow definition with Arn: ..........flow-definition/fraud-detector-a2i-1656277037953

```


We had configured API gateway to use an optional parameter as well 'flow_definition'. In the previous section this was not passed in
and defaults to "ignore", which skips the step for checking whether the data should be sent for human review or not. 
If an arn value for this is passed, then it will  also start a human loop for reviews if the model insight scores is
between the set threshold (700-900) as set in the lambda environment variables.  SCORE_THRESHOLD_MIN and "SCORE_THRESHOLD_MAX.  Note that this
range was chosen as it matches the rules associated with fraud detector for labelling the prediction for review. 
This uses Augmented AI service (described in the next section), to send the model scores which are 
within this range to check if the labels predicted from the model are accurate or need to be corrected via human review.
We will need to append the extra parameter `flow_definition` to the end of the query string as below. Replace <arn> with the arn value for flow definition 
which can be found from the console (navigate to AugmentedAI-> Human Review Workflow and use the workflow arn) from the human 
review workflow which was created in the previous command.
The choice of variables values below, should generate a fraud insight score within this range and hence trigger a human loop to be started.

```
curl -X GET https://d9d16i7hbc.execute-api.us-east-1.amazonaws.com/dev?trans_num=6cee353a9d618adfbb12ecad9d427244&amt=245.97&zip=97383&city=Stayton&first=Erica&job='Engineer, biomedical'&street='213 Girll Expressway'&category=shopping_pos&city_pop=116001&gender=F&cc_num=180046165512893&last=Walker&state=OR&merchant=fraud_Macejkovic-Lesch&event_timestamp=2020-10-13T09:21:53.000&flow_definition=<arn>
```

if this ran successfully, you should see the human loop in progress as in screenshot below.

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/human-loops-a2i.png"></img>

The log stream configured for lambda function can also be checked. The insight score is 872 and this should initiate the 
call to StartHumanLoop action and can be confirmed from the 'Started human loop: Fraud-detector' log message

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/fraud/predict-lambda-logs-human-loop.png"></img>


Similarly, to run this from the local machine, we can use the same script which we ran in the previous section to generate realtime predictions.
However, we need to pass in an extra argument `--flow_definition` with the arn value to enable HumanLoop. 
The example below uses payload which was marked for review from the model after batch prediction. When passed this
payload via the realtime api - it outputs the prediction results as well as starts a human loop.

```
$ python projects/fraud/predictions.py --predictions realtime --payload_path datasets/fraud-sample-data/dataset1/payload.json --detector_version 2 \
--role AmazonFraudDetectorRole --flow_definition <arn>
27-06-2022 02:51:31 : INFO : predictions : main : 170 : running realtime prediction
27-06-2022 02:51:31 : INFO : predictions : main : 186 : fraud score 858.0 between range thresholds 900 and 700
27-06-2022 02:51:31 : INFO : predictions : main : 193 : Human loop input:
27-06-2022 02:51:32 : INFO : predictions : main : 196 : Started human loop: Fraud-detector-1656294690802

[
    {
        "modelVersion": {
            "modelId": "fraud_model",
            "modelType": "ONLINE_FRAUD_INSIGHTS",
            "modelVersionNumber": "1.0"
        },
        "scores": {
            "fraud_model_insightscore": 858.0
        }
    }
]

{'ResponseMetadata': {'RequestId': '0ccebd34-50be-4552-871b-d88912bf4c31', 'HTTPStatusCode': 201, 'HTTPHeaders': {'date': 'Mon, 27 Jun 2022 01:51:31 GMT', 'content-type': 'application/json; charset=UTF-8', 'content-length': '240', 'connection': 'keep-alive', 'x-amzn-requestid': '0ccebd34-50be-4552-871b-d88912bf4c31', 'access-control-allow-origin': '*', 'x-amz-apigw-id': 'UW79mE9eoAMFY7A=', 'x-amzn-trace-id': 'Root=1-62b90d23-48517924671f237c42c46512'}, 'RetryAttempts': 0}, 'HumanLoopArn': 'arn:aws:sagemaker:us-east-1:376337229415:human-loop/Fraud-detector-1656294690802'}

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