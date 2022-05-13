import boto3
import shutil
import json
import click
from pathlib import Path
import os

iam_client = boto3.client("iam")
lambda_client = boto3.client("lambda")


@click.command()
@click.option("--function_name", help="Name of lambda resource to create")
@click.option(
    "--role", default="ReadObjectsS3forLambda", help="IAM role name for lambda resource"
)
@click.option("--timeout", default=20, help="Max allowable timeout for lambda")
def create_lambda_aws(
    function_name, role, timeout, handler="lambda_function.lambda_handler"
):
    os.chdir(Path(__file__).parent)
    shutil.make_archive(function_name, "zip", function_name)
    with open(f"{function_name}.zip", "rb") as f:
        lambda_zip = f.read()

    role = iam_client.get_role(RoleName=role)
    print(f"\n Role details: {json.dumps(role, default=str)} \n")

    response = lambda_client.create_function(
        FunctionName=function_name,
        Runtime="python3.9",
        Role=role["Role"]["Arn"],
        Handler=handler,
        Code=dict(ZipFile=lambda_zip),
        Timeout=timeout,  # Maximum allowable timeout
    )

    print(json.dumps(response, indent=4, default=str))


if __name__ == "__main__":
    create_lambda_aws()
