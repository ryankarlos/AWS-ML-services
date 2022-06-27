from diagrams import Diagram, Cluster
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.aws.ml import FraudDetector, AugmentedAi
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.security import Cognito
from diagrams.aws.management import Cloudwatch
from diagrams.aws.general import User

with Diagram("Diagram", show=True):
    Lambda_Batch = LambdaFunction("Lambda Batch Prediction")
    Lambda_RealTime = LambdaFunction("Lambda RealTime Prediction")
    S31 = SimpleStorageServiceS3("Batch Input")
    S32 = SimpleStorageServiceS3("Batch Results")
    AugAi = AugmentedAi("A2i")
    User1 = User("User")
    User2 = User("User")
    User3 = User("User")
    SQS_predict = SQS("SQS")
    SNS = SNS("SNS")
    Cognito = Cognito("Cognito")
    Fraud_Detector = FraudDetector("Fraud Detector")
    CloudWatch = Cloudwatch("CloudWatch Logs")

    with Cluster("Fraud Model and Rules"):
        fraud_detector_input = [
            FraudDetector("Model"),
            FraudDetector("Rules"),
            FraudDetector("Outcomes"),
        ]

    fraud_detector_input >> Fraud_Detector
    Lambda_Batch >> CloudWatch
    Lambda_RealTime >> CloudWatch
    User1 >> S31 >> SQS_predict >> Lambda_Batch >> Fraud_Detector >> SNS
    Fraud_Detector >> S32
    User2 >> Lambda_RealTime >> Fraud_Detector >> AugAi >> User3
    User3 >> AugAi
    User3 >> Cognito
    Cognito >> User3
