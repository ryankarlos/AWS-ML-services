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
    response = awslambda.get_function(FunctionName=lambda_function_name,)
    lambda_arn = response["Configuration"]["FunctionArn"]
    logger.info(f"Lambda arn {lambda_arn} for function {lambda_function_name}")
    return lambda_arn


def get_account_id():
    response = sts.get_caller_identity()
    account_id = response["Account"]
    return account_id


def create_bucket_notification_config(bucket_name, account_id, workflow, **kwargs):
    if workflow == "train":
        sfn_trigger_lambda_arn = kwargs["sfn_trigger_lambda_arn"]
        object_prefix_sfn_trigger_lambda = kwargs["object_prefix_sfn_trigger_lambda"]
        response = s3.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration={
                "LambdaFunctionConfigurations": [
                    {
                        "Id": "RawDataTriggerLambda",
                        "LambdaFunctionArn": sfn_trigger_lambda_arn,
                        "Events": ["s3:ObjectCreated:*"],
                        "Filter": {
                            "Key": {
                                "FilterRules": [
                                    {
                                        "Name": "prefix",
                                        "Value": object_prefix_sfn_trigger_lambda,
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
    elif workflow == "predict":
        batch_transform_lambda_arn = kwargs["batch_transform_lambda_arn"]
        batch_trigger_lambda_arn = kwargs["batch_trigger_lambda_arn"]
        object_prefix_batch_trigger_lambda = kwargs[
            "object_prefix_batch_trigger_lambda"
        ]
        object_prefix_batch_transform_lambda = kwargs[
            "object_prefix_batch_transform_lambda"
        ]
        response = s3.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration={
                "LambdaFunctionConfigurations": [
                    {
                        "Id": "BatchTriggerLambda",
                        "LambdaFunctionArn": batch_trigger_lambda_arn,
                        "Events": ["s3:ObjectCreated:*"],
                        "Filter": {
                            "Key": {
                                "FilterRules": [
                                    {
                                        "Name": "prefix",
                                        "Value": object_prefix_batch_trigger_lambda,
                                    },
                                    {"Name": "suffix", "Value": ".csv"},
                                ]
                            }
                        },
                    },
                    {
                        "Id": "BatchTransformLambda",
                        "LambdaFunctionArn": batch_transform_lambda_arn,
                        "Events": ["s3:ObjectCreated:*"],
                        "Filter": {
                            "Key": {
                                "FilterRules": [
                                    {
                                        "Name": "prefix",
                                        "Value": object_prefix_batch_transform_lambda,
                                    },
                                    {"Name": "suffix", "Value": ".out"},
                                ]
                            }
                        },
                    },
                ],
            },
            ExpectedBucketOwner=account_id,
            SkipDestinationValidation=True,
        )

    logger.info("HTTPStatusCode: %s", response["ResponseMetadata"]["HTTPStatusCode"])
    logger.info("RequestId: %s", response["ResponseMetadata"]["RequestId"])
    return response


@click.command()
@click.option(
    "--sfn_trigger_lambda_function_name",
    default="LambdaSFNTrigger",
    help="lambda function name which triggers step function job",
)
@click.option(
    "--batch_transform_function_name",
    default="LambdaBatchTransform",
    help="lambda function name which transforms batch personalize output data from s3",
)
@click.option(
    "--batch_trigger_lambda_function_name",
    default="LambdaBatchTrigger",
    help="lambda function name which triggers batch job in personalize",
)
@click.option(
    "--bucket_name",
    default="recommendation-sample-data",
    help="Bucket name for configuring notifications",
)
@click.option(
    "--object_prefix_batch_transform_lambda",
    default="movie-lens/batch/results/",
    help="updates to objects with this prefix to send notification to lambda to transform batch data",
)
@click.option(
    "--object_prefix_batch_trigger_lambda",
    default="movie-lens/batch/input/",
    help="object for which s3 event notification triggers lambda for starting batch job",
)
@click.option(
    "--object_prefix_sfn_trigger_lambda",
    default="movie-lens/raw_data/input/",
    help="updates to objects with this prefix to trigger lambda which starts step function job",
)
@click.option(
    "--workflow",
    default="train",
    type=click.Choice(["train", "predict"]),
    help="whether adding bucket notifications for train or predict workflow",
)
def main(
    sfn_trigger_lambda_function_name,
    batch_trigger_lambda_function_name,
    batch_transform_function_name,
    bucket_name,
    object_prefix_sfn_trigger_lambda,
    object_prefix_batch_trigger_lambda,
    object_prefix_batch_transform_lambda,
    workflow,
):
    account_id = get_account_id()
    kwargs = {}
    if workflow == "train":
        kwargs["sfn_trigger_lambda_arn"] = get_lambda_arn(
            sfn_trigger_lambda_function_name
        )
        kwargs["object_prefix_sfn_trigger_lambda"] = object_prefix_sfn_trigger_lambda
    elif workflow == "predict":
        kwargs["batch_trigger_lambda_arn"] = get_lambda_arn(
            batch_trigger_lambda_function_name
        )
        kwargs["batch_transform_lambda_arn"] = get_lambda_arn(
            batch_transform_function_name
        )
        kwargs[
            "object_prefix_batch_trigger_lambda"
        ] = object_prefix_batch_trigger_lambda
        kwargs[
            "object_prefix_batch_transform_lambda"
        ] = object_prefix_batch_transform_lambda
    response = create_bucket_notification_config(
        bucket_name, account_id, workflow, **kwargs
    )
    return response


if __name__ == "__main__":
    main()
