from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.aws.ml import FraudDetector, AugmentedAi
from diagrams.aws.integration import SQS
from diagrams.aws.security import Cognito
from diagrams.aws.general import User
from diagrams.aws.network import APIGateway

with Diagram("Diagram", show=True):
    Lambda_Batch = LambdaFunction("Lambda Batch Prediction")
    Lambda_RealTime = LambdaFunction("Lambda RealTime Prediction")
    APIGateway = APIGateway("API Gateway")
    S31 = SimpleStorageServiceS3("Batch Input")
    S32 = SimpleStorageServiceS3("Batch Results")
    S33 = SimpleStorageServiceS3("Human Loop Reviews")
    AugAi = AugmentedAi("A2i")
    User1 = User("User")
    User2 = User("User")
    User3 = User("User")
    SQS_predict = SQS("SQS")
    Cognito = Cognito("Cognito")

    with Cluster("Fraud Detector Rules and Outcomes"):
        fraud_detector_input = [
            FraudDetector("Model"),
            FraudDetector("Rules"),
            FraudDetector("Outcomes"),
        ]
        Fraud_Detector = FraudDetector("Fraud Detector")
        Fraud_Detector - Edge(color="brown", style="dotted") - fraud_detector_input

    User1 >> S31 >> SQS_predict >> Lambda_Batch >> Edge(
        color="red", style="bold"
    ) >> Fraud_Detector
    Fraud_Detector >> Edge(color="red", style="bold") >> S32
    User2 >> APIGateway >> Lambda_RealTime >> Edge(
        color="blue", style="bold"
    ) >> Fraud_Detector
    AugAi << Edge(color="blue", style="bold") << Fraud_Detector
    Lambda_RealTime >> APIGateway >> User2
    User3 >> Cognito >> AugAi
    AugAi >> S33
