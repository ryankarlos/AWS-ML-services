from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.aws.ml import FraudDetector
from diagrams.aws.integration import SQS, SNS, Eventbridge
from diagrams.aws.analytics import GlueCrawlers, GlueDataCatalog, Glue
from diagrams.aws.management import Cloudwatch
from diagrams.aws.general import User

with Diagram("Diagram", show=True, direction="LR"):
    Lambda_Glue = LambdaFunction("Lambda Glue")
    Lambda_Train = LambdaFunction("Lambda Train")
    S31 = SimpleStorageServiceS3("Raw Data")
    S32 = SimpleStorageServiceS3("Training Data")
    Eventbridge = Eventbridge("EventBridge")
    User1 = User("User")
    User2 = User("User")
    SQS_train = SQS("SQS")
    Fraud_Model = FraudDetector("Fraud Model")
    Glue_Job = Glue("Glue Job")
    Crawler = GlueCrawlers("GlueCrawler")
    Data_Catalog = GlueDataCatalog("GlueDataCatalog")
    CloudWatch = Cloudwatch("CloudWatch Logs")

    with Cluster("Fraud Event and Entity Types"):
        fraud_model_input = [
            FraudDetector("Fraud Variables"),
            FraudDetector("Fraud Labels"),
            FraudDetector("Fraud Entity Type"),
            FraudDetector("Fraud Event Type"),
        ]

    User2 >> Edge(label="check and deploy") >> Fraud_Model << fraud_model_input

    Lambda_Train >> CloudWatch

    Crawler >> Eventbridge >> Lambda_Glue >> Glue_Job >> S32
    Data_Catalog << Crawler << Edge(label="run crawler") << User1
    S31 >> Crawler
    Data_Catalog >> Glue_Job
    S32 >> SQS_train >> Lambda_Train >> Fraud_Model >> SNS
