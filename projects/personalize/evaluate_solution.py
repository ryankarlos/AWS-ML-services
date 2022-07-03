import boto3
import click

personalize = boto3.client("personalize")


@click.command()
@click.option(
    "--solution_arn", help="solution version arn for evaluating metrics",
)
def evaluate_solution_metrics(solution_arn):

    solution_version_description = personalize.describe_solution_version(
        solutionVersionArn=solution_arn
    )["solutionVersion"]
    print("Solution version status: " + solution_version_description["status"])

    # Use the solution ARN to get the solution status.
    solution_description = personalize.describe_solution(solutionArn=solution_arn)[
        "solution"
    ]
    solution_status = solution_description["status"]
    print("Solution status: " + solution_status)

    if solution_status == "ACTIVE":
        response = personalize.get_solution_metrics(solutionVersionArn=solution_arn)
        print(response["metrics"])
    else:
        print(
            f"cannot get solution metrics as solution status is not 'ACTIVE'. Solution status is in {solution_status} mode"
        )


if __name__ == "__main__":
    evaluate_solution_metrics()
