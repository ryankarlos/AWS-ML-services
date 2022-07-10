from diagrams import Diagram, Edge, Cluster
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.aws.ml import Personalize
from diagrams.aws.integration import SNS
from diagrams.aws.devtools import XRay
from diagrams.aws.general import User
from diagrams.aws.network import APIGateway

with Diagram("Diagram", show=False, direction="LR"):
    User1 = User("User")
    User2 = User("User")

    with Cluster("Batch Recommendation Workflow"):
        S31 = SimpleStorageServiceS3("Batch Data Input")
        S32 = SimpleStorageServiceS3("Raw Results")
        S33 = SimpleStorageServiceS3("Transformed Results ")
        LambdaBatch1 = LambdaFunction("Lambda")
        LambdaBatch2 = LambdaFunction("Lambda")
        Xray1 = XRay("XRay Traces")
        Xray2 = XRay("XRay Traces")
        SNS = SNS("SNS")
        BatchJob = Personalize("Personalize Batch Recommendation Job")
        User1 >> Edge(color="red", style="bold", label="Put raw data S3") >> S31 >> LambdaBatch1 >> Edge(style="bold",                                                                                        label="async invocation") >> BatchJob
        BatchJob >> S32 >> LambdaBatch2 >> S33 >> SNS
        LambdaBatch1 >> Xray1
        LambdaBatch2 >> Xray2
        SNS >> Xray2

    with Cluster("Real Time Recommendation Workflow"):
        APIGateway = APIGateway("API Gateway")
        LambdaRealTime = LambdaFunction("Lambda")
        Xray3 = XRay("XRay Traces")
        RealTime = Personalize("Personalize Real Time Recommendation")
        User2 >> Edge(color="blue", style="bold") >> APIGateway
        APIGateway >> LambdaRealTime >> RealTime >> LambdaRealTime
        LambdaRealTime >> APIGateway >> Edge(color="blue", style="bold") >> User2
        LambdaRealTime >> Xray3
        APIGateway >> Xray3







