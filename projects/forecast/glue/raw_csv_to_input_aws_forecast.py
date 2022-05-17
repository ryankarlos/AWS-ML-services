import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.transforms import *
import ast
from io import StringIO
import boto3
from pyspark.sql.functions import year, col
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(
    sys.argv, ["JOB_NAME", "database", "table", "destination", "year_range"]
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

bucket = args["destination"].split("//")[-1].rstrip("/")

try:
    assert len(ast.literal_eval(args["year_range"])) == 2
except AssertionError as e:
    raise ValueError(
        f"--year_range needs to have two values in str list passed as arg '[lower_year, upper_year]'.\
You passed in '{args['year_range']}'"
    )


# Adds an item id column as required by AWS Forecast. We pass in arbitary value 1.
# we can apply it to each record of the dynamic df using the map operator


def AddItemId(r):
    r["item_id"] = 1
    return r


ts_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="default",
    table_name="sample_manning_csv",
    transformation_ctx="read data from S3",
)

dyf_dropped = DropFields.apply(
    frame=ts_dyf, paths=["index"], transformation_ctx="drop index columnn"
)

dyf_applyMapping = ApplyMapping.apply(
    frame=dyf_dropped,
    mappings=[
        ("ds", "String", "timestamp", "timestamp"),
        ("y", "double", "target_value", "double"),
    ],
    transformation_ctx="rename and cast columns",
)

dyf_MapItemid = Map.apply(frame=dyf_applyMapping, f=AddItemId)

filter_years = ast.literal_eval(args["year_range"])
filtered_df = dyf_MapItemid.toDF().filter(
    (year(col("timestamp")) > filter_years[0])
    & (year(col("timestamp")) < filter_years[1])
)

final_dyf = DynamicFrame.fromDF(filtered_df.repartition(1), glueContext, "final_dyf")
glueContext.write_dynamic_frame.from_options(
    frame=final_dyf,
    connection_type="s3",
    connection_options={"path": args["destination"]},
    format="csv",
    transformation_ctx="S3 upload",
)

##### this bit below renames the file key in S3 as glue write_dynamic_frame creates random filename
### we also delete the original key after renaming

client = boto3.client("s3")
response = client.list_objects(Bucket=bucket, Prefix="run-")

objects = [item["Key"] for item in response["Contents"]]
print(objects)
max_date = max([item["LastModified"] for item in response["Contents"]])
print(max_date)
for item in response["Contents"]:
    if item["LastModified"] == max_date:
        key = item["Key"]

response = client.get_object(Bucket=bucket, Key=key)
bytes_data = response["Body"].read()

renamed = "glue_prep_aws_forecast.csv"
print(f"Renaming file {key} to {renamed}")
client.put_object(Body=bytes_data, Bucket=bucket, Key=renamed)

for item in objects:
    client.delete_object(Bucket=bucket, Key=item)

job.commit()
