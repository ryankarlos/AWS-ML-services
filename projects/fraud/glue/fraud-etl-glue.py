import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame
import boto3
from pyspark.sql.functions import *
import os

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "fraud_samples",
        "legit_samples",
        "bucket",
        "entity_type",
        "catalog_db",
        "catalog_table",
        "train_source_key",
        "test_source_key",
        "train_dest_key",
        "test_dest_key",
        "train_max_cut_off",
        "test_min_cut_off",
    ],
)
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)
print(args)


def sparkUnion(glueContext, unionType, mapping, transformation_ctx) -> DynamicFrame:
    for alias, frame in mapping.items():
        frame.toDF().createOrReplaceTempView(alias)
    result = spark.sql(
        "(select * from source1) UNION " + unionType + " (select * from source2)"
    )
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)


def sparkSqlQuery(glueContext, query, mapping, transformation_ctx) -> DynamicFrame:
    for alias, frame in mapping.items():
        frame.toDF().createOrReplaceTempView(alias)
    result = spark.sql(query)
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)


def write_output_to_s3(dyf, s3_path, prefix, renamed_key, transformation_ctx):

    client = boto3.client("s3")
    resource = boto3.resource("s3")

    print(f"saving dyanmic frame to S3 bucket with prefix path: {prefix}")
    # Script generated for node S3 bucket
    S3bucket_dyf = glueContext.write_dynamic_frame.from_options(
        frame=dyf,
        connection_type="s3",
        format="csv",
        connection_options={"path": s3_path},
        transformation_ctx=transformation_ctx,
    )

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.copy
    response = client.list_objects(Bucket=args["bucket"], Prefix=f"{prefix}/run-",)

    objectkey_to_rename = response["Contents"][0]["Key"]

    copy_output = {"Bucket": args["bucket"], "Key": objectkey_to_rename}

    print(f"renaming filename to {renamed_key} as glue output filename is random")

    resource.meta.client.copy(copy_output, args["bucket"], renamed_key)
    print(f"deleting original output {objectkey_to_rename}....")
    response = client.delete_object(Bucket=args["bucket"], Key=objectkey_to_rename)


# set these but they should not overlap
TRAIN_MAX_TIMESTAMP = args["train_max_cut_off"]
TEST_MIN_TIMESTAMP = args["test_min_cut_off"]

fraud_samples = args["fraud_samples"]
legit_samples = args["legit_samples"]


# Script generated for node SQL
SqlQuery0 = f"""
select * from 
(
    (
    select * from myDataSource
    where EVENT_LABEL == 'fraud'
    order BY RAND() 
    limit {fraud_samples}
    ) 
    union all
    (
    select * from myDataSource
    where EVENT_LABEL == 'legit'
    order BY RAND() 
    limit {legit_samples}
    )
)

"""


bucket = args["bucket"]
train_input_key = args["train_source_key"]
test_input_key = args["test_source_key"]

# Uncomment below if wanting to use S3 as source instead of glue data catalog

#
# train_dyF = glueContext.create_dynamic_frame.from_options(
#     "s3", {"paths": [f"s3://{bucket}/{train_input_key}"]}, "csv", {"withHeader": True}
# )
# test_dyF = glueContext.create_dynamic_frame.from_options(
#     "s3", {"paths": [f"s3://{bucket}/{test_input_key}"]}, "csv", {"withHeader": True}
# )
#
#
# Union_node_dyf = sparkUnion(
#     glueContext,
#     unionType="ALL",
#     mapping={
#         "source1": train_dyF,
#         "source2": test_dyF,
#     },
#     transformation_ctx="Union_train_test",
# )
#
#
# Union_node_dyf.count()
#
# mappings = [
#     ("trans_date_trans_time", "string", "trans_date_trans_time", "timestamp"),
#     ("cc_num", "string", "cc_num", "bigint"),
#     ("merchant", "string", "merchant", "string"),
#     ("category", "string", "category", "string"),
#     ("amt", "string", "amt", "float"),
#     ("first", "string", "first", "string"),
#     ("last", "string", "last", "string"),
#     ("gender", "string", "gender", "string"),
#     ("street", "string", "street", "string"),
#     ("city", "string", "city", "string"),
#     ("state", "string", "state", "string"),
#     ("zip", "string", "zip", "int"),
#     ("lat", "string", "lat", "float"),
#     ("long", "string", "long", "float"),
#     ("city_pop", "string", "city_pop", "int"),
#     ("job", "string", "job", "string"),
#     ("dob", "string", "dob", "date"),
#     ("trans_num", "string", "trans_num", "string"),
#     ("unix_time", "string", "unix_time", "int"),
#     ("merch_lat", "string", "merch_lat", "float"),
#     ("merch_long", "string", "merch_long", "float"),
#     ("is_fraud", "string", "is_fraud", "binary"),
# ]


# comment out this if uncommenting out the code above which reads from S3 as source
Union_node_dyf = glueContext.create_dynamic_frame_from_catalog(
    database=args["catalog_db"],
    table_name=args["catalog_table"],
    transformation_ctx="Read fraud train and test combined data from catalog table ",
)
Union_node_dyf.count()

# This mapping is customised for catalog table inferred schema.
# comment this out if uncommenting out the code above which reads from S3 as source
mappings = [
    ("trans_date_trans_time", "string", "trans_date_trans_time", "timestamp"),
    ("cc_num", "long", "cc_num", "long"),
    ("merchant", "string", "merchant", "string"),
    ("category", "string", "category", "string"),
    ("amt", "double", "amt", "double"),
    ("first", "string", "first", "string"),
    ("last", "string", "last", "string"),
    ("gender", "string", "gender", "string"),
    ("street", "string", "street", "string"),
    ("city", "string", "city", "string"),
    ("state", "string", "state", "string"),
    ("zip", "long", "zip", "long"),
    ("lat", "double", "lat", "double"),
    ("long", "double", "long", "double"),
    ("city_pop", "long", "city_pop", "int"),
    ("job", "string", "job", "string"),
    ("dob", "string", "dob", "date"),
    ("trans_num", "string", "trans_num", "string"),
    ("unix_time", "long", "unix_time", "int"),
    ("merch_lat", "double", "merch_lat", "double"),
    ("merch_long", "double", "merch_long", "double"),
    (
        "is_fraud",
        "long",
        "is_fraud",
        "short",
    ),  # seems to drop all rows if casting to binary so use short
]

# Script generated for node ApplyMapping
ApplyMapping_dyf = ApplyMapping.apply(
    frame=Union_node_dyf, mappings=mappings, transformation_ctx="ApplyMapping",
)
ApplyMapping_dyf.printSchema()


# Script generated for node Drop Fields
DropFields_dyf = DropFields.apply(
    frame=ApplyMapping_dyf,
    paths=["col0", "merch_lat", "merch_long", "lat", "long", "unix_time", "dob"],
    transformation_ctx="DropFields",
)

DropFields_dyf.printSchema()


df = DropFields_dyf.toDF()


df = df.withColumn("EVENT_TIMESTAMP", col("trans_date_trans_time")).withColumn(
    "EVENT_LABEL", col("is_fraud")
)
df.show()

train_df = df.filter(col("EVENT_TIMESTAMP") < args["train_max_cut_off"]).withColumn(
    "EVENT_LABEL",
    when(col("EVENT_LABEL") == "0", "legit").when(col("EVENT_LABEL") == "1", "fraud"),
)
test_df = df.filter(df.EVENT_TIMESTAMP > args["test_min_cut_off"]).withColumn(
    "EVENT_LABEL",
    when(col("EVENT_LABEL") == "0", "legit").when(col("EVENT_LABEL") == "1", "fraud"),
)


train_df.select(col("EVENT_TIMESTAMP"), col("EVENT_LABEL")).orderBy(
    desc("EVENT_TIMESTAMP")
).show(truncate=False)


test_df_adapted = (
    test_df.withColumn("ENTITY_TYPE", lit(args["entity_type"]))
    .withColumn("ENTITY_ID", lit("unknown"))
    .withColumn("EVENT_ID", col("trans_num"))
)


test_dyf = DynamicFrame.fromDF(test_df_adapted, glueContext, "test_dyf")
train_dyf = DynamicFrame.fromDF(train_df, glueContext, "train_dyf")


train_dyf = DropFields.apply(
    frame=train_dyf,
    paths=["is_fraud", "trans_date_trans_time"],
    transformation_ctx="Drop_train_metadata_fields",
)


test_dyf = DropFields.apply(
    frame=test_dyf,
    paths=["is_fraud", "trans_date_trans_time"],
    transformation_ctx="Drop_test_metadata_fields",
)


sampled_test_dyf = sparkSqlQuery(
    glueContext,
    query=SqlQuery0,
    mapping={"myDataSource": test_dyf},
    transformation_ctx="SQLQuery_test_sample",
)
sampled_test_dyf.count()


sampled_test_dyf.toDF().show()

# reparition to single df to avoid saving multiple paritions in s3 bucket

single_part_train_dyf = DynamicFrame.fromDF(
    train_dyf.toDF().repartition(1), glueContext, "single_partition_train"
)
single_part_test_dyf = DynamicFrame.fromDF(
    sampled_test_dyf.toDF().repartition(1), glueContext, "single_partition_test_sample"
)

# we don't need event label column in sampled dataset as fraud detector batch prediction will not work
# if event label is present
single_part_test_dyf = DropFields.apply(
    frame=single_part_test_dyf,
    paths=["EVENT_LABEL"],
    transformation_ctx="Drop_label_batch_sample",
)


train_dest_split = args["train_dest_key"].split("/")
train_filename = train_dest_split.pop(-1)
renamed_key = args["train_dest_key"]
transformation_ctx = "S3bucket_write_train_dyf"
prefix = "/".join(train_dest_split)
s3_path = os.path.join("s3://", args["bucket"], prefix)

print("")
print("Saving training data ......")
write_output_to_s3(
    single_part_train_dyf, s3_path, prefix, renamed_key, transformation_ctx
)

test_dest_split = args["test_dest_key"].split("/")
test_filename = test_dest_split.pop(-1)
renamed_key = args["test_dest_key"]
transformation_ctx = "S3bucket_write_test_dyf"
prefix = "/".join(test_dest_split)
s3_path = os.path.join("s3://", args["bucket"], prefix)

print("Saving test data ......")
write_output_to_s3(
    single_part_test_dyf, s3_path, prefix, renamed_key, transformation_ctx
)

job.commit()
