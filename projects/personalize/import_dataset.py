import boto3
import click

personalize = boto3.client("personalize")


@click.command()
@click.option(
    "--s3_input_path",  default="s3://recommendation-sample-data/movie-lens/transformed/model_input/interactions.csv", help="path to input s3 for bulk import",
)
@click.option(
    "--job_name",   default="MoviesDatasetImport", help="Name of job",
)
@click.option(
    "--dataset_arn",
    help="arn of dataset resource created in personalize to import data into ",
)
@click.option(
    "--role_arn", help="arn of role which has access to S3",
)
def import_datatset_to_personalize(s3_input_path, job_name, dataset_arn, role_arn):
    response = personalize.create_dataset_import_job(
        jobName=job_name,
        datasetArn=dataset_arn,
        dataSource={"dataLocation": s3_input_path},
        roleArn=role_arn,
    )

    dsij_arn = response["datasetImportJobArn"]

    print("Dataset Import Job arn: " + dsij_arn)

    description = personalize.describe_dataset_import_job(datasetImportJobArn=dsij_arn)[
        "datasetImportJob"
    ]

    print("Name: " + description["jobName"])
    print("ARN: " + description["datasetImportJobArn"])
    print("Status: " + description["status"])
    return response


if __name__ == "__main__":
    import_datatset_to_personalize()
