import pandas as pd
import boto3

s3_client = boto3.client("s3")
iam = boto3.client("iam")
fraudDetector = boto3.client("frauddetector")


INPUT_BUCKET = "fraud-sample-data"
DATA_KEY = "input/fraudTrain_glue_transformed.csv"
DETECTOR_NAME = "fraud_detector_demo"
MODEL_NAME = "fraud_model"
ENTITY_TYPE = "customer"
EVENT_TYPE = "credit_card_transaction"
MODEL_TYPE = "ONLINE_FRAUD_INSIGHTS"
MODEL_VERSION = "1"
DETECTOR_VERSION = "1"
REGION = "us-east-1"
ROLE_NAME = "FraudDetectorRoleS3Access"


def get_training_variables():
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=INPUT_BUCKET, Key=DATA_KEY)
    df = pd.read_csv(response.get("Body"))
    variables = df.columns.values.tolist()
    variables.pop(-1)
    variables.pop(-1)
    return variables


def train_fraud_model():
    try:
        fraudDetector.create_model(
            modelId=MODEL_NAME,
            eventTypeName=EVENT_TYPE,
            modelType=MODEL_TYPE,
        )
    except fraudDetector.exceptions.ValidationException:
        pass

    variables = get_training_variables()

    fraudDetector.create_model_version(
        modelId=MODEL_NAME,
        modelType=MODEL_TYPE,
        trainingDataSource="EXTERNAL_EVENTS",
        trainingDataSchema={
            "modelVariables": variables,
            "labelSchema": {"labelMapper": {"FRAUD": ["fraud"], "LEGIT": ["legit"]}},
        },
        externalEventsDetail={
            "dataLocation": f"s3://{INPUT_BUCKET}/{DATA_KEY}",
            "dataAccessRoleArn": iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"],
        },
    )


if __name__ == "__main__":
    train_fraud_model()
