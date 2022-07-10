from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.aws.ml import Personalize
from diagrams.aws.integration import SQS
from diagrams.aws.analytics import Glue
from diagrams.aws.devtools import XRay
from diagrams.aws.general import User
from diagrams.aws.integration import StepFunctions


with Diagram("Diagram", show=False, direction="LR"):
    Lambda_SFN = LambdaFunction("Lambda SFN")
    S31 = SimpleStorageServiceS3("Raw Data")
    S32 = SimpleStorageServiceS3("Training Data")
    S33 = SimpleStorageServiceS3("Metadata")
    User1 = User("User")
    Xray = XRay("XRay Traces")
    StepFunctions = StepFunctions("Step Function")

    with Cluster("Step Function Components"):
        Glue = Glue("Glue Job")
        ImportDataset = Personalize("Personalize Import Dataset")
        Solution = Personalize("Personalize Solution")
        sfn_components = [Glue, ImportDataset, Solution]
        Glue >> ImportDataset >> Solution
        Glue >> S32
        Glue >> S33

    User1 >> S31 >> Lambda_SFN >> StepFunctions
    StepFunctions >> sfn_components
    StepFunctions >> Xray
    Lambda_SFN >> Xray
