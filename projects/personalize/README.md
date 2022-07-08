
### AWS Personalize Examples

There are a number of datasets that are available for recommendation research. Amongst them, the MovieLens dataset https://movielens.org/ is 
probably one of the more popular ones. MovieLens is a non-commercial web-based movie recommender system. It is created in 1997 and 
run by GroupLens, a research lab at the University of Minnesota, in order to gather movie rating data for research purposes. 
MovieLens data has been critical for several research studies including personalized recommendation and social psychology.

Download the zip MovieLens 25M Dataset under 'Recommended for new research' section in https://grouplens.org/datasets/movielens/
From command line, we can unzip this as below. Navigate to the folder where the zip is stored and run the unzip comand.
You may need to install the unzip package if not already installed https://www.tecmint.com/install-zip-and-unzip-in-linux/. 
For example on ubuntu `sudo apt-get install -y unzip`.
We do not require the genome-tags.csv and genome-scores.csv so these can be deleted

```
$ cd datasets/personalize
$ unzip ml-25m.zip
Archive:  datasets/personalize/ml-25m.zip
   creating: ml-25m/
  inflating: ml-25m/tags.csv
  inflating: ml-25m/links.csv
  inflating: ml-25m/README.txt
  inflating: ml-25m/ratings.csv
  inflating: ml-25m/genome-tags.csv
  inflating: ml-25m/genome-scores.csv
  inflating: ml-25m/movies.csv

```

 ### Loading data into S3 


The following example sets Status=Enabled to enable Transfer Acceleration on a bucket. You use Status=Suspended to suspend Transfer Acceleration.

```
$ aws s3api put-bucket-accelerate-configuration --bucket recommendation-sample-data --accelerate-configuration Status=Enabled

```

It's a best practice to use aws s3 commands (such as aws s3 cp) for multipart uploads and downloads, because these aws s3 commands automatically perform multipart uploading and downloading based on the file size
https://aws.amazon.com/premiumsupport/knowledge-center/s3-multipart-upload-cli/
To use more of your host's bandwidth and resources during the upload, increase the maximum number of concurrent requests set in your AWS CLI configuration. By default, the AWS CLI uses 10 maximum concurrent requests. This command sets the maximum concurrent number of requests to 20:

You can direct all Amazon S3 requests made by s3 and s3api AWS CLI commands to the accelerate endpoint: s3-accelerate.amazonaws.com. To do this, set the configuration value use_accelerate_endpoint to true in a profile in your AWS Config file. Transfer Acceleration must be enabled on your bucket to use the accelerate endpoint.
The following example uploads a file to a bucket enabled for Transfer Acceleration by using the --endpoint-url parameter to specify the accelerate endpoint.

```
$ aws configure set default.s3.use_accelerate_endpoint true
$ aws configure set default.s3.max_concurrent_requests 20
$ aws s3 cp datasets/personalize/ml-25m/ s3://recommendation-sample-data/movie-lens/raw_data/ --region us-east-1 --recursive --endpoint-url https://recommendation-sample-data.s3-accelerate.amazonaws.com

upload: datasets\personalize\ml-25m\links.csv to s3://recommendation-sample-data/movie-lens/links.csv
upload: datasets\personalize\ml-25m\input\movies.csv to s3://recommendation-sample-data/movie-lens/movies.csv
upload: datasets\personalize\ml-25m\README.txt to s3://recommendation-sample-data/movie-lens/README.txt
upload: datasets\personalize\ml-25m\tags.csv to s3://recommendation-sample-data/movie-lens/tags.csv
upload: datasets\personalize\ml-25m\input\ratings.csv to s3://recommendation-sample-data/movie-lens/ratings.csv

```

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/s3_raw_data.png"></img>

Finally we need to add the glue script and lambda function to S3 bucket as well. This assumes the lambda function is zipped 
as in `lambdas/data_import_personalize.zip` and you have a bucket with key `aws-glue-assets-376337229415-us-east-1/scripts`. If not adapt
the query accordingly. Run the following commands from root of the repo

```
$ aws s3 cp step_functions/personalize-definition.json s3://recommendation-sample-data/movie-lens/personalize-definition.json

upload: step_functions/personalize-definition.json to s3://recommendation-sample-data/movie-lens/personalize-definition.json

```

```
$ aws s3 cp lambdas/trigger_glue_personalize.zip s3://recommendation-sample-data/movie-lens/lambda/trigger_glue_personalize.zip

upload: lambdas\trigger_glue_personalize.zip to s3://recommendation-sample-data/movie-lens/lambda/trigger_glue_personalize.zip

```

```
$ aws configure set default.s3.use_accelerate_endpoint false
$ aws s3 cp projects/personalize/glue/Personalize_Glue_Script.py s3://aws-glue-assets-376337229415-us-east-1/scripts/Personalize_Glue_Script.py

upload: projects\personalize\glue\Personalize_Glue_Script.py to s3://aws-glue-assets-376337229415-us-east-1/scripts/Personalize_Glue_Script.py

```

If not configured transfer acceleration for the default glue assets bucket then can set to false before running cp command.
Otherwise, you will get the error
`An error occurred (InvalidRequest) when calling the PutObject operation: S3 Transfer Acceleration is not configured on this bucket`


### CloudFormation Templates

Create cloudformation template which creates the follwing resources:

* Glue Job 
* Personalize resources (Dataset, DatasetGroup, Schema) and associated role 
* Step Function (for running ETL and Personalize DatasetImport Job and Creating solution version) and associated role
* lambda function (and associated role) for triggering step function execution with S3 event notification.

```
 $ aws cloudformation create-stack --stack-name PersonalizeGlue \
 --template-body file://cloudformation/personalize.yaml \
 --capabilities CAPABILITY_NAMED_IAM

{
    "StackId": "arn:aws:cloudformation:<region>:<account-id>:stack/PersonalizeGlue/2dc9cca0-fe63-11ec-b51b-0e44449cc4eb"
}

```

### S3 event notifications

We need to configure two S3 event notifications:

* S3 to lambda notification (for put raw data object event) to trigger the step function execution
* send notifications to SNS topic created from cloudformation, when the batch jobs from Personalize complete.  

* For SNS, we have configured email as subscriber to SNS via protocol set as email endpoint.
The SNS messages will then send email to subscriber address when event message received from S3.

From root of repo, run the following script to configure bucket notifications. 

```
$ python projects/personalize/put_notification_s3.py
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
INFO:__main__:Lambda arn arn:aws:lambda:........:function:LambdaSFNTrigger for function LambdaSFNTrigger
INFO:__main__:Topic arn arn:aws:sns:........:personalize-batch for personalize-batch
INFO:__main__:HTTPStatusCode: 200
INFO:__main__:RequestId: X6X9E99JE13YV6RH
{'ResponseMetadata': {'RequestId': 'X6X9E99JE13YV6RH', 'HostId': 'yAseQ1ugcv9FKbRFxCps6MjeMnG7QFjQDVmRjhs5JQXeHjmYqzcCXH/+j1cOlz3vRiEBDhZPOnQ=', 
'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amz-id-2': 'yAseQ1ugcv9FKbRFxCps6MjeMnG7QFjQDVmRjhs5JQXeHjmYqzcCXH/+j1cOlz3vRiEBDhZPOnQ=', 
'x-amz-request-id': 'X6X9E99JE13YV6RH', 'date': 'Fri, 08 Jul 2022 03:04:55 GMT', 'server': 'AmazonS3', 'content-length': '0'}, 'RetryAttempts': 0}}

```

Note: There is currently not support for notifications to FIFO type SNS topics. 

#### Run GlueJob via Notebook and Train Solution Manually

Create GlueDev endpoint using CloudFormation stack `cloudformation\glue-dev-endpoint.yaml`

Set the parameters 
* NumberofWorkers = 7
* WorkerType = G.1X

Then create notebook using this endpoint and upload `projects\personalize\glue\notebook\Personalize_GLue.ipynb`

Once the notebook has finished running, you should see two folders in `s3://recommendation-sample-data/movie-lens/transformed/` as below. 
Each of these will contain a csv file corresponding to the interactions data (which will be used for training solution) and 
additional metadata (i.e. columns with movie genres, ratings etc)

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/s3_glue_output.png"></img>

We can then import dataset into personalize by running the following script:

```
$ python projects/personalize/import_dataset.py --dataset_arn arn:aws:personalize:us-east-1:376337229415:dataset/RecommendGroup/INTERACTIONS --role_arn arn:aws:iam::376337229415:role/PersonalizeRole
Dataset Import Job arn: arn:aws:personalize:us-east-1:376337229415:dataset-import-job/MoviesDatasetImport
Name: MoviesDatasetImport
ARN: arn:aws:personalize:us-east-1:376337229415:dataset-import-job/MoviesDatasetImport
Status: CREATE PENDING
```

From the AWS console, create a training solution. Go to Solutions and Recipes -> Create Solution and fill in the 
values as in the screenshot below and then click `Create and train solution`

* Solution name: PersonalizeModel
* Solutiontype: Item recommendation
* Recipe: aws-user-personalization
* Advanced Configuration - Turn on 'Perform HPO'. Leave the other parameter values as it is.

The User-Personalization (aws-user-personalization) recipe is optimized for all User_Personalization recommendation scenarios. 
When recommending items, this recipe uses automatic item exploration.
https://docs.aws.amazon.com/personalize/latest/dg/native-recipe-new-item-USER_PERSONALIZATION.html

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/create_solution_console.png"></img>

Wait for solution version to print an ACTIVE status. The solution should train for about 1 hour. 

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/personalize_solution_user-personalization_recipe_with_HPO"></img>

