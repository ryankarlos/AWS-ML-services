import boto3
import click
import json

personalize_rec = boto3.client(service_name="personalize")
personalizeRt = boto3.client("personalize-runtime")


def create_batch_segment_job(
    input_s3_path, output_s3_path, job_name, num_users, role_arn, sol_ver_arn
):
    """
    create a batch segment job with the CreateBatchSegmentJob operation
    https://docs.aws.amazon.com/personalize/latest/dg/recommendations.html
    :param input_s3_path:Amazon S3 path to your input file
    :param output_s3_path: Amazon S3 path to your output location
    :param job_name:name of job
    :param num_users:number of users you want Amazon Personalize to predict for each line of input data
    :param role_arn:ARN of the IAM service role you created for Amazon Personalize during set up.
    :param sol_ver_arn: Amazon Resource Name (ARN) of your solution version
    :return:
    """
    response = personalize_rec.create_batch_segment_job(
        solutionVersionArn=sol_ver_arn,
        jobName=job_name,
        numResults=num_users,
        roleArn=role_arn,
        jobInput={"s3DataSource": {"path": input_s3_path}},
        jobOutput={"s3DataDestination": {"path": output_s3_path}},
    )
    return response


def create_batch_inference_job(
    input_s3_path, output_s3_path, job_name, role_arn, sol_ver_arn, weight, cutoff,
):
    """
    Create a batch inference job to get batch item recommendations for users based on input data from Amazon S3.
    https://docs.aws.amazon.com/personalize/latest/dg/recommendations.html
    :param input_s3_path:Amazon S3 path to your input file
    :param output_s3_path:Amazon S3 path to your output location
    :param job_name:name of job
    :param role_arn:ARN of the IAM service role which has read and write access to input and output Amazon S3 buckets respectively.
    :param sol_ver_arn:Amazon Resource Name (ARN) of your solution version
    :param weight:User-Personalization recipe specific itemExplorationConfig hyperparameter, explorationWeight. Defaults to 0.3
    :param cutoff:User-Personalization recipe specific itemExplorationConfig hyperparameter, explorationcutoff. Defaults to 30
    :return:
    """
    response = personalize_rec.create_batch_inference_job(
        solutionVersionArn=sol_ver_arn,
        jobName=job_name,
        roleArn=role_arn,
        batchInferenceJobConfig={
            "itemExplorationConfig": {
                "explorationWeight": f"{weight}",
                "explorationItemAgeCutOff": f"{cutoff}",
            }
        },
        jobInput={"s3DataSource": {"path": input_s3_path}},
        jobOutput={"s3DataDestination": {"path": output_s3_path}},
    )
    return response


def get_real_time_recommendations(campaign_arn, user_id, num_results, **context):
    """
    To get personalized recommendations or similar item recommendations from an Amazon Personalize campaign.
    If your campaign uses contextual metadata (for requirements see Increasing recommendation relevance with
    contextual metadata)
    optionally provide context data.For each context, for the Key, enter the metadata field, and for the Value, enter
    the context data.
    e.g. the key could be DEVICE and the value could be mobile phone.
    https://docs.aws.amazon.com/personalize/latest/dg/recommendations.html
    :param campaign_arn:Arn of campaign created
    :param user_id:user ID that is in the data that you used to train the solution
    :param num_results:number of recommended items. Defaults to 10
    :param context: To get a recommendation based on contextual metadata. provide the metadata field as the key and the
    context data as the value.
    :return:
    """

    if context:
        response = personalizeRt.get_recommendations(
            campaignArn=campaign_arn, userId=user_id, context=context
        )
    else:
        response = personalizeRt.get_recommendations(
            campaignArn=campaign_arn, userId=user_id, numResults=num_results
        )

    print("Recommended items")
    for item in response["itemList"]:
        print(item["itemId"])
    return response


@click.command()
@click.option(
    "--s3_input_path", help="path to input s3 data for batch recommendations",
)
@click.option(
    "--s3_output_path",
    help="path to output s3 folder for stroring batch prediction results",
)
@click.option(
    "--job_name", help="Name of job",
)
@click.option(
    "--sol_arn", help="arn of solution version to use",
)
@click.option(
    "--role_arn", help="arn of role which has access to S3",
)
@click.option(
    "--num_users",
    default=10,
    help="number of users to predict for in each line of input data",
)
@click.option(
    "--weight",
    default=0.3,
    help="User-Personalization recipe specific itemExplorationConfig hyperparameter, explorationWeight",
)
@click.option(
    "--cutoff",
    default=30,
    help="User-Personalization recipe specific itemExplorationConfig hyperparameter, explorationcutoff",
)
@click.option(
    "--campaign_arn", help="For realtime recommendation. Arn of campaign",
)
@click.option(
    "--user_id",
    help="For real time recommendation. user ID that is in the data that you used to train the solution",
)
@click.option(
    "--num_results",
    default=10,
    help="number of recommended items for real time recommendation",
)
@click.option(
    "--context",
    defualt="{}",
    help="optional context metadata for realt time prediction. If left as default, will run recommendations without "
    "context and num_results param needs to be passed.",
)
@click.option(
    "--recommendation_mode",
    default="batch_inference",
    type=click.Choice(["batch_inference", "batch_segment", "realtime"]),
    help="whether to generate batch or realtime predictions",
)
def main(
    recommendation_mode,
    s3_input_path,
    s3_output_path,
    job_name,
    sol_arn,
    role_arn,
    num_users,
    weight,
    cutoff,
    campaign_arn,
    user_id,
    num_results,
    context,
):
    if recommendation_mode == "batch_inference":
        return create_batch_inference_job(
            s3_input_path, s3_output_path, job_name, role_arn, sol_arn, weight, cutoff,
        )
    elif recommendation_mode == "batch_segment":
        return create_batch_segment_job(
            s3_input_path, s3_output_path, job_name, num_users, role_arn, sol_arn
        )
    elif recommendation_mode == "realtime":
        context = json.loads(context)
        return get_real_time_recommendations(
            campaign_arn, user_id, num_results, **context
        )
    else:
        raise ValueError(
            f"inference mode must be either 'batch_inference', 'batch_segment' or 'realtime'. You specified "
            f"{recommendation_mode}"
        )


if __name__ == "__main__":
    main()
