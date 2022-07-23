from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.aws.ml import Personalize
from diagrams.aws.analytics import Glue
from diagrams.aws.devtools import XRay
from diagrams.aws.general import User
from diagrams.aws.integration import StepFunctions


with Diagram("Diagram", show=False, direction="LR"):
    Lambda_SFN = LambdaFunction("Lambda SFN")
    S31 = SimpleStorageServiceS3("S3")
    S32 = SimpleStorageServiceS3("formatted training data")
    S33 = SimpleStorageServiceS3("metadata")
    User1 = User("User")
    Xray = XRay("XRay Traces")
    StepFunctions = StepFunctions("Step Function")

    with Cluster("Step Function Components"):
        Glue = Glue("Glue Job")
        ImportDataset = Personalize("Personalize Import Dataset")
        Solution = Personalize("Personalize Solution")
        sfn_components = [Glue, ImportDataset, Solution]
        S31 >> Edge(color="brown", style="dashed") >> Glue
        Glue >> Edge(color="darkgreen") >> ImportDataset >> Edge(
            color="darkgreen"
        ) >> Solution
        Glue >> Edge(color="brown") >> S32
        Glue >> Edge(color="brown") >> S33
        S32 >> Edge(color="darkgreen", style="dashed") >> ImportDataset

    User1 >> Edge(label="upload raw csv data") >> S31 >> Lambda_SFN >> StepFunctions
    StepFunctions >> Edge(color="darkgreen") >> sfn_components
    StepFunctions >> Edge(color="darkorange") >> Xray
    Lambda_SFN >> Edge(color="darkorange") >> Xray
