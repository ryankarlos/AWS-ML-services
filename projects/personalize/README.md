
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
upload: datasets\personalize\ml-25m\movies.csv to s3://recommendation-sample-data/movie-lens/movies.csv
upload: datasets\personalize\ml-25m\README.txt to s3://recommendation-sample-data/movie-lens/README.txt
upload: datasets\personalize\ml-25m\tags.csv to s3://recommendation-sample-data/movie-lens/tags.csv
upload: datasets\personalize\ml-25m\ratings.csv to s3://recommendation-sample-data/movie-lens/ratings.csv

```

Finally we need to add the glue script and lambda function to S3 bucket as well. This assumes the lambda function is zipped 
as in `lambdas/data_import_personalize.zip` and you have a bucket with key `aws-glue-assets-376337229415-us-east-1/scripts`. If not adapt
the query accordingly. Run the following commands from root of the repo

```
$ aws s3 cp lambdas/data_import_personalize.zip s3://recommendation-sample-data/lambda/data_import_personalize.zip
```

```
$ aws s3 cp projects/personalize/glue/movies_glue_etl.py s3://aws-glue-assets-376337229415-us-east-1/scripts/personalize-glue-etl-movies.py
```