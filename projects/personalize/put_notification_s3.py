import logging
import boto3
import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
s3 = boto3.client("s3")
sns = boto3.client("sns")
sts = boto3.client("sts")
awslambda = boto3.client("lambda")


def get_sns_topic_arn(topic_name):
    response = sns.list_topics()
    topic_arn = [
        topic["TopicArn"]
        for topic in response["Topics"]
        if topic["TopicArn"].split(":")[-1] == topic_name
    ][0]

    logger.info(f"Topic arn {topic_arn} for {topic_name}")
    return topic_arn


def get_lambda_arn(lambda_function_name):
    response = awslambda.get_function(
        FunctionName=lambda_function_name,
    )
    lambda_arn = response["Configuration"]["FunctionArn"]
    logger.info(f"Lambda arn {lambda_arn} for function {lambda_function_name}")
    return lambda_arn


def get_account_id():
    response = sts.get_caller_identity()
    account_id = response["Account"]
    return account_id


def create_bucket_notification_config(
    bucket_name,
    object_prefix_sns,
    object_prefix_lambda,
    topic_arn,
    lambda_arn,
    account_id,
):
    response = s3.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            "TopicConfigurations": [
                {
                    "Id": "BatchResultsSNS",
                    "TopicArn": topic_arn,
                    "Events": ["s3:ObjectCreated:*"],
                    "Filter": {
                        "Key": {
                            "FilterRules": [
                                {
                                    "Name": "prefix",
                                    "Value": object_prefix_sns,
                                },
                                {"Name": "suffix", "Value": ".csv"},
                            ]
                        }
                    },
                }
            ],
            "LambdaFunctionConfigurations": [
                {
                    "Id": "RawDataTriggerLambda",
                    "LambdaFunctionArn": lambda_arn,
                    "Events": ["s3:ObjectCreated:*"],
                    "Filter": {
                        "Key": {
                            "FilterRules": [
                                {
                                    "Name": "prefix",
                                    "Value": object_prefix_lambda,
                                },
                                {"Name": "suffix", "Value": ".csv"},
                            ]
                        }
                    },
                }
            ],
        },
        ExpectedBucketOwner=account_id,
        SkipDestinationValidation=True,
    )

    print(response)
    logger.info("HTTPStatusCode: %s", response["ResponseMetadata"]["HTTPStatusCode"])
    logger.info("RequestId: %s", response["ResponseMetadata"]["RequestId"])
    return response


@click.command()
@click.option(
    "--topic_name",
    default="personalize-batch",
    help="SNS topic name for target s3 notification",
)
@click.option(
    "--lambda_function_name",
    default="LambdaSFNTrigger",
    help="lambda function name for target s3 notification",
)
@click.option(
    "--bucket_name",
    default="recommendation-sample-data",
    help="Bucket name for configuring notifications",
)
@click.option(
    "--object_prefix_sns",
    default="movie-lens/batch/results/",
    help="updates to objects with this prefix to send notification to SNS",
)
@click.option(
    "--object_prefix_lambda",
    default="movie-lens/raw_data/input/",
    help="updates to objects with this prefix to trigger lambda",
)
def main(
    topic_name,
    lambda_function_name,
    bucket_name,
    object_prefix_sns,
    object_prefix_lambda,
):
    account_id = get_account_id()
    lambda_arn = get_lambda_arn(lambda_function_name)
    topic_arn = get_sns_topic_arn(topic_name)
    response = create_bucket_notification_config(
        bucket_name,
        object_prefix_sns,
        object_prefix_lambda,
        topic_arn,
        lambda_arn,
        account_id,
    )
    return response


if __name__ == "__main__":
    main()
