import sys
import logging
import boto3
import click

logger = logging.getLogger("evaluate")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

personalize = boto3.client("personalize")


@click.command()
@click.option(
    "--solution_version_arn",
    help="solution version arn for active solution version for evaluating metrics",
)
def evaluate_solution_metrics(solution_version_arn):

    solution_version_description = personalize.describe_solution_version(
        solutionVersionArn=solution_version_arn
    )["solutionVersion"]
    logger.info("Solution version status: " + solution_version_description["status"])
    response = personalize.get_solution_metrics(solutionVersionArn=solution_version_arn)
    logger.info(f"Metrics: \n\n {response['metrics']}")


if __name__ == "__main__":
    evaluate_solution_metrics()
