import boto3

s3_client = boto3.client("s3")
iam = boto3.client("iam")
fraudDetector = boto3.client("frauddetector")

INPUT_BUCKET = "fraud-sample-data"
DATA_KEY = "glue_transformed/fraudTrain.csv"
DETECTOR_NAME = "fraud_detector_demo"
MODEL_NAME = "fraud_model"
ENTITY_TYPE = "customer"
EVENT_TYPE = "credit_card_transaction"
MODEL_TYPE = "ONLINE_FRAUD_INSIGHTS"
MODEL_VERSION = "1"
DETECTOR_VERSION = "1"
REGION = "us-east-1"
ROLE_NAME = "FraudDetectorRoleS3Access"
MODE= "update"


def get_training_variables():
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=INPUT_BUCKET, Key=DATA_KEY)
    variables_str = response.get("Body").read().decode("utf-8")
    variables = variables_str.rstrip("\n").split(",")
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
        print("Created model container for training")
    except fraudDetector.exceptions.ValidationException:
        print("Model container already exists so proceeding to model training ....")

    variables = get_training_variables()

    print(f"Starting model training with variables {variables}....")

    try:
        if MODE == "create":
            print(f"Training new model and incrementing major version")
            response = fraudDetector.create_model_version(
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
            return response
        elif MODE == "update":
            print(f"Training model and updating existing major model version {MODEL_VERSION}")
            response = fraudDetector.update_model_version(
                modelId=MODEL_NAME,
                modelType=MODEL_TYPE,
                majorVersionNumber=MODEL_VERSION,
                externalEventsDetail={
                    "dataLocation": f"s3://{INPUT_BUCKET}/{DATA_KEY}",
                    "dataAccessRoleArn": iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"],
                },
            )
            return response
    except fraudDetector.exceptions.ValidationException as e:
        if "Simultaneous training" in e.value:
            print("Model Version already training")
        else:
            print(e)
            raise


if __name__ == "__main__":
    train_fraud_model()
