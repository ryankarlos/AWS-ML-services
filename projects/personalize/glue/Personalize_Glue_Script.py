import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrameCollection
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "s3_input_path",
        "bucket",
        "s3_output_prefix",
        "rating_repartition_number",
        "ratings_resample_fraction",
    ],
)
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)
print(args)

s3_input_path = args["s3_input_path"]


def RenameS3ItemsUsersData(glueContext, dfc) -> DynamicFrameCollection:
    BUCKET_NAME = args["bucket"]
    PREFIX = args["s3_output_prefix"]
    S3_PATH = f"s3://{BUCKET_NAME}/{PREFIX}/model_input/"
    import boto3

    client = boto3.client("s3")
    S3bucket_dyf = glueContext.write_dynamic_frame.from_options(
        frame=dfc,
        connection_type="s3",
        format="csv",
        connection_options={"path": S3_PATH},
    )

    response = client.list_objects(
        Bucket=BUCKET_NAME,
        Prefix=f"{PREFIX}/model_input/run-",
    )
    name = response["Contents"][0]["Key"]
    print(name)

    client.copy_object(
        Bucket=BUCKET_NAME,
        CopySource=f"{BUCKET_NAME}/{name}",
        Key=f"{PREFIX}/model_input/interactions.csv",
    )
    client.delete_object(Bucket=BUCKET_NAME, Key=name)


def RenameS3Metadata(glueContext, dfc) -> DynamicFrameCollection:
    BUCKET_NAME = args["bucket"]
    PREFIX = args["s3_output_prefix"]
    S3_PATH = f"s3://{BUCKET_NAME}/{PREFIX}/metadata/"
    import boto3

    client = boto3.client("s3")
    S3bucket_dyf = glueContext.write_dynamic_frame.from_options(
        frame=dfc,
        connection_type="s3",
        format="csv",
        connection_options={"path": S3_PATH},
    )

    response = client.list_objects(
        Bucket=BUCKET_NAME,
        Prefix=f"{PREFIX}/metadata/run-",
    )
    name = response["Contents"][0]["Key"]
    print(name)

    client.copy_object(
        Bucket=BUCKET_NAME,
        CopySource=f"{BUCKET_NAME}/{name}",
        Key=f"{PREFIX}/metadata/metadata.csv",
    )
    client.delete_object(Bucket=BUCKET_NAME, Key=name)


# Script generated for node S3 input movies
S3inputmovies_node1656882361110 = glueContext.create_dynamic_frame.from_options(
    format_options={
        "quoteChar": '"',
        "withHeader": True,
        "separator": ",",
        "optimizePerformance": True,
    },
    connection_type="s3",
    format="csv",
    connection_options={"paths": [f"{s3_input_path}/movies.csv"]},
    transformation_ctx="S3inputmovies_node1656882361110",
)

# Script generated for node S3 input ratings
S3inputratings_node1656882568718 = glueContext.create_dynamic_frame.from_options(
    format_options={
        "quoteChar": '"',
        "withHeader": True,
        "separator": ",",
        "optimizePerformance": False,
    },
    connection_type="s3",
    format="csv",
    connection_options={
        "paths": [f"{s3_input_path}/ratings.csv"],
        "recurse": True,
    },
    transformation_ctx="S3inputratings_node1656882568718",
)

resampledratings_dyf = DynamicFrame.fromDF(
    S3inputratings_node1656882568718.toDF().sample(
        False, float(args["ratings_resample_fraction"]), seed=0
    ),
    glueContext,
    "resampled ratings",
)

repartitioned_df = resampledratings_dyf.toDF().repartition(
    int(args["rating_repartition_number"])
)

repartitioned_dyf = DynamicFrame.fromDF(
    repartitioned_df,
    glueContext,
    "repartitioned ratings",
)


# Script generated for node Renamed keys for Join
RenamedkeysforJoin_node1656883045941 = ApplyMapping.apply(
    frame=repartitioned_dyf,
    mappings=[
        ("userId", "bigint", "userId", "long"),
        ("movieId", "bigint", "`(right) movieId`", "long"),
        ("rating", "double", "rating", "double"),
        ("timestamp", "bigint", "timestamp", "long"),
    ],
    transformation_ctx="RenamedkeysforJoin_node1656883045941",
)

# Script generated for node Join
Join_node1656883036773 = Join.apply(
    frame1=S3inputmovies_node1656882361110,
    frame2=RenamedkeysforJoin_node1656883045941,
    keys1=["movieId"],
    keys2=["`(right) movieId`"],
    transformation_ctx="Join_node1656883036773",
)


# Script generated for node Split Fields
SplitFields_node1656884127492 = SplitFields.apply(
    frame=Join_node1656883036773,
    paths=["genres", "title", "`(right) movieId`"],
    name2="SplitFields_node16568841274921",
    name1="SplitFields_node16568841274920",
    transformation_ctx="SplitFields_node1656884127492",
)

# Script generated for node Dataframe interactions
Dataframeinteractions_node1656884315834 = SelectFromCollection.apply(
    dfc=SplitFields_node1656884127492,
    key=list(SplitFields_node1656884127492.keys())[1],
    transformation_ctx="Dataframeinteractions_node1656884315834",
)

# Script generated for node Dataframe movie metadata
Dataframemoviemetadata_node1656884256844 = SelectFromCollection.apply(
    dfc=SplitFields_node1656884127492,
    key=list(SplitFields_node1656884127492.keys())[0],
    transformation_ctx="Dataframemoviemetadata_node1656884256844",
)


# Script generated for node Map field names interactions
Mapfieldnamesinteractions_node1656884351305 = ApplyMapping.apply(
    frame=Dataframeinteractions_node1656884315834,
    mappings=[
        ("movieId", "string", "ITEM_ID", "long"),
        ("userId", "string", "USER_ID", "long"),
        ("timestamp", "string", "TIMESTAMP", "long"),
    ],
    transformation_ctx="Mapfieldnamesinteractions_node1656884351305",
)

# Script generated for node Map field name metdata
Mapfieldnamemetdata_node1656884427706 = ApplyMapping.apply(
    frame=Dataframemoviemetadata_node1656884256844,
    mappings=[
        ("title", "string", "TITLE", "string"),
        ("genres", "string", "GENRES", "string"),
        ("(right) movieId", "string", "ITEM_ID", "long"),
    ],
    transformation_ctx="Mapfieldnamemetdata_node1656884427706",
)


# Script generated for node Drop Duplicates Interactions
DropDuplicatesInteractions_node1656884507578 = DynamicFrame.fromDF(
    Mapfieldnamesinteractions_node1656884351305.toDF().dropDuplicates(),
    glueContext,
    "DropDuplicatesInteractions_node1656884507578",
)

# Script generated for node Drop Duplicates Metadata
DropDuplicatesMetadata_node1656884924120 = DynamicFrame.fromDF(
    Mapfieldnamemetdata_node1656884427706.toDF().dropDuplicates(),
    glueContext,
    "DropDuplicatesMetadata_node1656884924120",
)


single_part_interactions_dyf = DynamicFrame.fromDF(
    DropDuplicatesInteractions_node1656884507578.toDF().repartition(1),
    glueContext,
    "single_partition_interactions",
)

single_part_metadata_dyf = DynamicFrame.fromDF(
    DropDuplicatesMetadata_node1656884924120.toDF().repartition(1),
    glueContext,
    "single_partition_metadata",
)


RenameInteractionsfileinS3_node1656886003325 = RenameS3ItemsUsersData(
    glueContext,
    DynamicFrameCollection(
        {"single_partition_interactions": single_part_interactions_dyf}, glueContext
    ),
)


RenameMetadatafileinS3_node1656885522913 = RenameS3Metadata(
    glueContext,
    DynamicFrameCollection(
        {"single_partition_metadata": single_part_metadata_dyf}, glueContext
    ),
)


job.commit()
