import os
import logging
import boto3
import urllib.parse
import json
import csv
import io

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")

metadata_key = os.environ["METADATA_KEY"]


def lambda_handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    results_key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    results_obj = s3.get_object(Bucket=bucket, Key=results_key)
    metadata_obj = s3.get_object(Bucket=bucket, Key=metadata_key)
    lines = metadata_obj["Body"].read().decode("latin")
    buf = io.StringIO(lines)
    reader = csv.DictReader(buf, delimiter=",")
    metadata_rows = list(reader)
    bytes_list = results_obj["Body"].read().rstrip(b"").split(b"\n")
    result = []
    for data in bytes_list:
        if data != b"":
            results_dict = json.loads(data.decode("utf-8"))
            if results_dict["error"] is None:
                recommended_items = results_dict["output"]["recommendedItems"]
                recomendations = []
                for row in metadata_rows:
                    if row["movieId"] in recommended_items:
                        recommend = (
                            row["title"]
                            + " "
                            + "("
                            + row["genres"].split("|", 1)[0]
                            + ")"
                        )
                        recomendations.append(recommend)
                recomendations = " | ".join(recomendations)
                data = {
                    "user_id": results_dict["input"]["userId"],
                    "recommendations": recomendations,
                }
                result.append(data)
    # transformed_batch = pd.DataFrame(result)
    print(result)
    header = ["user_id", "recommendations"]
    data_dict_keys = result[0].keys()
    results_key = f'{results_key.rsplit("/", 1)[0]}/transformed_users.csv'
    # creating a file buffer
    file_buff = io.StringIO()
    # writing csv data to file buffer
    writer = csv.DictWriter(file_buff, fieldnames=data_dict_keys)
    writer.writeheader()
    for data in result:
        writer.writerow(data)
    # placing file to S3, file_buff.getvalue() is the CSV body for the file
    s3.put_object(Body=file_buff.getvalue(), Bucket=bucket, Key=results_key)
    return result
