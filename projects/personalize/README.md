
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

Create cloudformation template which creates the following resources:

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

If successful, we should see the following resources successfully created in the resources tab

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/cloud_formation_parameters_tab.png"></img>

If we run the command as above, just using the default parameters, we should see the key value pairs listed in the parameters
tab as in screenshot below.

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/cloud_formation_resources_tab.png"></img>

We should see that all the services should be created. For example navigate to the Step function console and click on the 
sfn name `GlueETLPersonalizeTraining`

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/step_function_diagram_with_definition_console.png"></img>


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


#### Trigger Workflow for Training Solution


<img width=500 src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/personalize_train.png"></img>


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/s3_glue_output.png"></img>

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/train_app_service_map_xray.png"></img>


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/xray_trace_lambda.png"></img>

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/xray_traces_sfn.png"></img>

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/CloudWatch_Xraytraces_timeline1.png"></img>

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/CloudWatch_Xraytraces_timeline2.png"></img>



<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/sfn_successful_run_create_new_sol.png"></img>


#### Run GlueJob via Notebook and Train Solution Manually

Create GlueDev endpoint using CloudFormation stack `cloudformation\glue-dev-endpoint.yaml`

Set the parameters 
* NumberofWorkers = 7
* WorkerType = G.1X

Then create notebook using this endpoint and upload `projects\personalize\glue\notebook\Personalize_GLue.ipynb`

Once the notebook has finished running, you should see two folders in `s3://recommendation-sample-data/movie-lens/transformed/` as below. 
Each of these will contain a csv file corresponding to the interactions data (which will be used for training solution) and 
additional metadata (i.e. columns with movie genres, ratings etc)

NOTE: The notebook by default samples half the number of rows in the ratings csv which is still around 12.5 million rows.
This can result in a large bill if training a model (as mentioned in previous section).
You may want to adjust the fraction parameter to sample method, to a lower value (e.g. 0.05) and check the ratings 
dataframe row count afterwards.

```
resampledratings_dyf = DynamicFrame.fromDF(
    S3inputratings_node1656882568718.toDF().sample(False, 0.5, seed=0),
    glueContext,
    "resampled ratings",
)


resampledratings_dyf.toDF().count()
```


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

Wait for solution version to print an ACTIVE status. Training can take a while, depending on the dataset size and number of user-item
interactions. If using AutoMl this can take longer. Be careful, that the training time (hrs) value is  based on 1 hr of compute capacity 
(default is 4CPU and 8GiB memory). However, this can be automatically adjusted if more efficient instance type is chosen to 
train the data in order to complete the job more quickly. In this case, the training hours metric computed will be adjusted and increased , 
resulting in a larger bill. Assume the interactions dataset is created from 12 million rows of the ratings csv in glue ETL job (e.g. if we set
the glue parameter ,
this can result in 560 training hours, and over $130 bill ! 

#### Evaluating solution metrics 

You can use offline metrics to evaluate the performance of the trained model before you create a campaign and provide recommendations. 
Offline metrics allow you to view the effects of modifying a solution's hyperparameters or compare results from models trained with the same data.
https://docs.aws.amazon.com/personalize/latest/dg/working-with-training-metrics.html
To get performance metrics, Amazon Personalize splits the input interactions data into a training set and a testing set. The split depends on the type of recipe you choose:
For USER_SEGMENTATION recipes, the training set consists of 80% of each user's interactions data and the testing set consists of 20% of each user's interactions data.
For all other recipe types, the training set consists of 90% of your users and their interactions data. The testing set consists of the remaining 10% of users and their interactions data.
Amazon Personalize then creates the solution version using the training set. After training completes, Amazon Personalize gives the new solution version the oldest 90% of each user’s 
data from the testing set as input. Amazon Personalize then calculates metrics by comparing the recommendations the solution version generates to the actual interactions in the 
newest 10% of each user’s data from the testing set. https://docs.aws.amazon.com/personalize/latest/dg/working-with-training-metrics.html

<img width=500 src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/personalize_solution_user-personalization_recipe_with_HPO.png"></img>

You retrieve the metrics for a the trained solution version above, by running the following script, which calls the GetSolutionMetrics operation with  
`solutionVersionArn` parameter

```
python projects/personalize/evaluate_solution.py --solution_version_arn <solution-version-arn>
2022-07-09 20:31:24,671 - evaluate - INFO - Solution version status: ACTIVE
2022-07-09 20:31:24,787 - evaluate - INFO - Metrics:

 {'coverage': 0.1233, 'mean_reciprocal_rank_at_25': 0.1208, 'normalized_discounted_cumulative_gain_at_10': 0.1396, 'normalized_discounted_cumulative_gain_at_25': 0.1996, 'normalized_discounted_cumulative_gain_at_5': 0.1063, 'precision_at_10': 0.0367, 'precision_at_25': 0.0296, 'precision_at_5': 0.0423}
```

The above metrics are described below :

* coverage : An evaluation metric that tells you the proportion of unique items that Amazon Personalize might recommend using your model 
out of the total number of unique items in Interactions and Items datasets. To make sure Amazon Personalize recommends more of your items, 
use a model with a higher coverage score. Recipes that feature item exploration, such as User-Personalization, have higher coverage than those that 
don’t, such as popularity-count.
https://docs.aws.amazon.com/personalize/latest/dg/working-with-training-metrics.html

* mean reciprocal rank at 25
An evaluation metric that assesses the relevance of a model’s highest ranked recommendation. Amazon Personalize calculates this metric 
using the average accuracy of the model when ranking the most relevant recommendation out of the top 25 recommendations over all requests for recommendations.
This metric is useful if you're interested in the single highest ranked recommendation.
https://docs.aws.amazon.com/personalize/latest/dg/working-with-training-metrics.html


* normalized discounted cumulative gain (NCDG) at K (5/10/25)
An evaluation metric that tells you about the relevance of your model’s highly ranked recommendations, where K is a sample size of 5, 10, or 25 recommendations. 
Amazon Personalize calculates this by assigning weight to recommendations based on their position in a ranked list, where each recommendation is 
discounted (given a lower weight) by a factor dependent on its position. The normalized discounted cumulative gain at K assumes that recommendations that 
are lower on a list are less relevant than recommendations higher on the list.
Amazon Personalize uses a weighting factor of 1/log(1 + position), where the top of the list is position 1.
This metric rewards relevant items that appear near the top of the list, because the top of a list usually draws more attention.
https://docs.aws.amazon.com/personalize/latest/dg/working-with-training-metrics.html


* precision at K
An evaluation metric that tells you how relevant your model’s recommendations are based on a sample size of K (5, 10, or 25) recommendations. 
Amazon Personalize calculates this metric based on the number of relevant recommendations out of the top K recommendations, divided by K, 
where K is 5, 10, or 25. This metric rewards precise recommendation of the relevant items.
https://docs.aws.amazon.com/personalize/latest/dg/working-with-training-metrics.html

  
#### Creating Campaign for realtime recommendations

A campaign is a deployed solution version (trained model) with provisioned dedicated transaction capacity for creating 
real-time recommendations for your application users.  After you complete Preparing and importing data and Creating a solution, you are ready to 
deploy your solution version by creating an AWS Personalize Campaign
https://docs.aws.amazon.com/personalize/latest/dg/campaigns.html
If you are getting batch recommendations, you don't need to create a campaign.

```
$ python projects/personalize/deploy_solution.py --campaign_name MoviesCampaign --sol_version_arn <solution_version_arn> --mode create

2022-07-09 21:12:08,412 - deploy - INFO - Name: MoviesCampaign
2022-07-09 21:12:08,412 - deploy - INFO - ARN: arn:aws:personalize:........:campaign/MoviesCampaign
2022-07-09 21:12:08,412 - deploy - INFO - Status: CREATE PENDING
```

An additional arh `--config` can be passed, to set the explorationWeight and explorationItemAgeCutOff parameters for user
personalizaion recipe https://docs.aws.amazon.com/personalize/latest/dg/native-recipe-new-item-USER_PERSONALIZATION.html#bandit-hyperparameters
These parameters default to 0.3 and 30.0 respectively if not passed (as in previous example)
To set the explorationWeight and ItemAgeCutoff to 0.6 and 100 respectively, run the script as below:

```
$ python projects/personalize/deploy_solution.py --campaign_name MoviesCampaign --sol_version_arn <solution_version_arn> \
--config "{\"itemExplorationConfig\":{\"explorationWeight\":\"0.6\",\"explorationItemAgeCutOff\":\"100\"}}" --mode create

2022-07-09 21:12:08,412 - deploy - INFO - Name: MoviesCampaign
2022-07-09 21:12:08,412 - deploy - INFO - ARN: arn:aws:personalize:........:campaign/MoviesCampaign
2022-07-09 21:12:08,412 - deploy - INFO - Status: CREATE PENDING
```

#### Recommendations


<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/personalize/personalize_recommendation_workflow.png"></img>


You get real-time recommendations from Amazon Personalize with a campaign created earlier to give movie recommendations.
To increase recommendation relevance, include contextual metadata for a user, such as their device type or the time of day, when you get recommendations or get a personalized ranking.
https://docs.aws.amazon.com/personalize/latest/dg/getting-real-time-recommendations.html


With the User-Personalization recipe, Amazon Personalize generates scores for items based on a user's interaction data and metadata. 
These scores represent the relative certainty that Amazon Personalize has in whether the user will interact with the item next. 
Higher scores represent greater certainty.
https://docs.aws.amazon.com/personalize/latest/dg/recommendations.html

Amazon Personalize scores all of the items in your catalog relative to each other on a scale from 0 to 1 (both inclusive), so that the total of 
all scores equals 1. For example, if you're getting movie recommendations for a user and there are three movies in the Items dataset, 
their scores might be 0.6, 0.3, and 0.1. Similarly, if you have 1,000 movies in your inventory, the highest-scoring movies might have very 
small scores (the average score would be.001), but, because scoring is relative, the recommendations are still valid.
https://docs.aws.amazon.com/personalize/latest/dg/recommendations.html

We can run the following script, passing in the solution version arn, campaign arn, role name, user id and setting 
recommendation mode to realtime.
So for user `1`, the model recommends movies of drama/romance theme.

```
python projects/personalize/recommendations.py --job_name Moviesrealtimerecommend --sol_arn <solution-arn> --role_name PersonalizeRole \
--campaign_arn <campaign-arn> --user_id 1 --recommendation_mode realtime
2022-07-09 21:22:46,038 - recommendations - INFO - Generating 10 recommendations for user 1 using campaign arn:aws:personalize:........:campaign/MoviesCampaign
2022-07-09 21:22:46,646 - recommendations - INFO - Recommended items:

Bad Education (La mala educaci▒n) (2004) (Drama|Thriller)
Eternal Sunshine of the Spotless Mind (2004) (Drama|Romance|Sci-Fi)
Nobody Knows (Dare mo shiranai) (2004) (Drama)
Good bye, Lenin! (2003) (Comedy|Drama)
Man Without a Past, The (Mies vailla menneisyytt▒) (2002) (Comedy|Crime|Drama)
Amelie (Fabuleux destin d'Am▒lie Poulain, Le) (2001) (Comedy|Romance)
Talk to Her (Hable con Ella) (2002) (Drama|Romance)
Motorcycle Diaries, The (Diarios de motocicleta) (2004) (Adventure|Drama)
Very Long Engagement, A (Un long dimanche de fian▒ailles) (2004) (Drama|Mystery|Romance|War)
In the Mood For Love (Fa yeung nin wa) (2000) (Drama|Romance)
```

User `40` has been recommended crime/drama themed movies.

```
Kill Bill: Vol. 2 (2004) (Action|Drama|Thriller)
Little Miss Sunshine (2006) (Adventure|Comedy|Drama)
Snatch (2000) (Comedy|Crime|Thriller)
There Will Be Blood (2007) (Drama|Western)
Last King of Scotland, The (2006) (Drama|Thriller)
Trainspotting (1996) (Comedy|Crime|Drama)
Mystic River (2003) (Crime|Drama|Mystery)
No Country for Old Men (2007) (Crime|Drama)
Sin City (2005) (Action|Crime|Film-Noir|Mystery|Thriller)
Platoon (1986) (Drama|War)
```

User `162540` is interesting and seems to have recommended a combination of children/comedy and action/thriller 
genre movies based on users interactions.

```
Ice Age 2: The Meltdown (2006) (Adventure|Animation|Children|Comedy)
I Am Legend (2007) (Action|Horror|Sci-Fi|Thriller|IMAX)
Shrek the Third (2007) (Adventure|Animation|Children|Comedy|Fantasy)
2 Fast 2 Furious (Fast and the Furious 2, The) (2003) (Action|Crime|Thriller)
Saw II (2005) (Horror|Thriller)
300 (2007) (Action|Fantasy|War|IMAX)
Fight Club (1999) (Action|Crime|Drama|Thriller)
Night at the Museum (2006) (Action|Comedy|Fantasy|IMAX)
Dark Knight, The (2008) (Action|Crime|Drama|IMAX)
Hancock (2008) (Action|Adventure|Comedy|Crime|Fantasy)
```

We can also limit the number of results by passing in value for arg `--num_results`, which defaults to 10.
So for example, for `--user_id 15000` , we can get the top 4 results   

```
Kiss the Girls (1997) (Crime|Drama|Mystery|Thriller)
Scream (1996) (Comedy|Horror|Mystery|Thriller)
Firm, The (1993) (Drama|Thriller)
Wild Things (1998) (Crime|Drama|Mystery|Thriller)
```

To get batch recommendations, you use a batch inference job. A batch inference job is a tool that imports your batch input data from an Amazon 
S3 bucket, uses your solution version to generate item recommendations, and then exports the recommendations to an Amazon S3 bucket.
The input data can be a list of users or items or list of users each with a collection of items in JSON format. Use a batch inference 
job when you want to get batch item recommendations for your users or find similar items across an inventory.
To get user segments, you use a batch segment job. A batch segment job is a tool that imports your batch input data from an Amazon
S3 bucket, uses your solution version trained with a USER_SEGMENTATION recipe to generate user segments for each row of input 
data, and exports the segments to an Amazon S3 bucket. Each user segment is sorted in descending order based on the probability that 
each user will interact with items in your inventory. https://docs.aws.amazon.com/personalize/latest/dg/recommendations-batch.html

The input data in S3 needs to be a json file with the data in a specific format as specified in https://docs.aws.amazon.com/personalize/latest/dg/batch-data-upload.html#batch-recommendations-json-examples
For this example we will use a sample as in `datasets\personalize\ml-25m\batch\input\users.json` and upload this to S3 bucket `recommendation-sample-data` in
`movie-lens/batch/input/users.json`. The following script uses the default s3 bucket name `recommendation-sample-data` and input data key `movie-lens/batch/input/users.json`.
These can be overridden by passing a value to the `--bucket` and `--batch_input_key` args respectively. The results output will be stored in `movie-lens/batch/results/`
but a different path can be chosen by passing a path to `--batch_results_key` arg.

```
$ python projects/personalize/recommendations.py --job_name BatchInferenceMovies --num_results 25 --sol_arn arn:aws:personalize:.........:solution/PersonalizeModel/03c184cc --role_name PersonalizeRole
2022-07-10 05:50:55,409 - recommendations - INFO - Running batch inference job BatchInferenceMovies with config: {"itemExplorationConfig": {"explorationWeight": "0.3", "explorationItemAgeCutOff": "30"}}
2022-07-10 05:50:56,140 - recommendations - INFO - Response:

 {
     'batchInferenceJobArn': 'arn:aws:personalize:.......:batch-inference-job/BatchInferenceMovies', 
     'ResponseMetadata': 
        {
            'RequestId': 'e9cf11a6-ce65-456b-b17c-a4c55d858e5a', 
            'HTTPStatusCode': 200, 
            'HTTPHeaders': 
                {
                    'date': 'Sun, 10 Jul 2022 04:50:57 GMT', 
                    'content-type': 'application/x-amz-json-1.1', 
                    'content-length': '110', 
                    'connection': 'keep-alive', 
                    'x-amzn-requestid': 'e9cf11a6-ce65-456b-b17c-a4c55d858e5a'
                }, 
                    'RetryAttempts': 0
        }
 }

```

The results file `users.json.out` should be stored in destination folder specified `movie-lens/batch/results/`.
An example of the results is stored in `atasets\personalize\ml-25m\batch\results\users.json.out`
The format is as described https://docs.aws.amazon.com/personalize/latest/dg/batch-data-upload.html#batch-recommendations-json-examples
and each line contains a json with the input user id and the output recommended item ids, in this case 25 recommendations since we specified this in api call.

We can then retrieve the movie title and genres by mapping the `item_id` to title in movies.csv file.