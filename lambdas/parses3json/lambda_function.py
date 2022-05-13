import json
import boto3


def lambda_handler(event, context):
    s3 = boto3.resource("s3")
    obj = s3.Object(event["BucketName"], event["TranscribeOutputKey"]).get()
    big_str = json.loads(obj["Body"].read().decode("utf-8"))
    transcribed_text = big_str["results"]["transcripts"][0]["transcript"]
    print(transcribed_text)
    return {"TranscribedText": transcribed_text}
