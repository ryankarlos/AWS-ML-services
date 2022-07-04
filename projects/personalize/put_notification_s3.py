import logging
import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
topic_name = "personalize-batch"
s3 = boto3.client("s3")
sns = boto3.client("sns")
sts = boto3.client("sts")


response = sns.list_topics()
topic_arn = [
    topic["TopicArn"]
    for topic in response["Topics"]
    if topic["TopicArn"].split(":")[-1] == topic_name
][0]

print(topic_arn)


response = sts.get_caller_identity()
account_id = response["Account"]
response = s3.put_bucket_notification_configuration(
    Bucket="recommendation-sample-data",
    NotificationConfiguration={
        "TopicConfigurations": [
            {
                "TopicArn": topic_arn,
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {"Name": "prefix", "Value": "movie-lens/batch/results/"},
                            {"Name": "suffix", "Value": ".csv"},
                        ]
                    }
                },
            }
        ]
    },
    ExpectedBucketOwner=account_id,
    SkipDestinationValidation=True
)

print(response)
logger.info("HTTPStatusCode: %s", response["ResponseMetadata"]["HTTPStatusCode"])
logger.info("RequestId: %s", response["ResponseMetadata"]["RequestId"])
