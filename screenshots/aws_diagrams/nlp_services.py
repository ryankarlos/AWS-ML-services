from diagrams import Diagram, Edge, Cluster
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.aws.ml import Translate, Transcribe, Polly, Comprehend
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import StepFunctions
from diagrams.aws.general import User

with Diagram("NLP workflow for speech translation", show=True, direction="LR"):

    S31 = SimpleStorageServiceS3("S3 video object key")
    S32 = SimpleStorageServiceS3("S3 Transcribed")
    S33 = SimpleStorageServiceS3("S3 Translated mp3")
    User1 = User("User")

    CloudWatch = Cloudwatch("CloudWatch Logs")
    with Cluster("Step function tasks"):
        Lambda_Parse = LambdaFunction("Parse data")
        Transcribe = Transcribe("Transcribe")
        Translate = Translate("Translate")
        Polly = Polly("Polly")
        Comprehend = Comprehend("Comprehend \n (Sentiment, \n Syntax, \n Key Phrases,\n Entities)")
        StepFunctions = StepFunctions("Step function")
    User1 >> Edge(label="upload to S3") >> S31 >> Transcribe >> S32
    S32 >> Lambda_Parse >> Translate >> Comprehend >> S33
    Translate >> Polly >> S33
    CloudWatch << Lambda_Parse
