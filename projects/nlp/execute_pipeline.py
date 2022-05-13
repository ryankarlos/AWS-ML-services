from step_functions.state_machine_resource import execute_state_machine
import click


@click.command()
@click.option("--sf_name", help="Name of step function to execute")
@click.option("--target_lang_code", help="Lang to translate video into")
@click.option(
    "--voice_id",
    help="Polly voice id for synthesising text to speech. Must be available with neural engine option in AWS Polly",
)
@click.option(
    "--deploy/--no-deploy",
    default=False,
    help="Flag to determine whether to deploy new step function or not before execution",
)
@click.option(
    "--bucket",
    default="awstestnlp",
    help="s3 bucket containing the source and output files",
)
@click.option(
    "--s3_uri",
    default="s3://awstestnlp/source/transcribe-sample.5fc2109bb28268d10fbc677e64b7e59256783d3c.mp3",
    help="s3 uti for source mp3 video",
)
@click.option(
    "--transcribe_output_key",
    default="transcribed/transcribed.json",
    help="object key for storing output of transcription job in bucket",
)
@click.option(
    "--polly_output_key",
    default="polly/text_to_speech.mp3",
    help="object key for storing output of polly job in bucket",
)
@click.option(
    "--source_lang_code", default="en-US", help="language code for source video"
)
@click.option(
    "--job_name",
    default="Test",
    help="Name of transcription job to execute in step function",
)
@click.option(
    "--sf_role",
    default="StepFunctionAWSNLPServices",
    help="Name of IAM role assumed by step function",
)
def execute_nlp_state_machine(
    sf_name,
    target_lang_code,
    bucket,
    s3_uri,
    source_lang_code,
    job_name,
    transcribe_output_key,
    polly_output_key,
    voice_id,
    deploy,
    sf_role,
):
    sf_input = {
        "BucketName": bucket,
        "Source": s3_uri,
        "TranscribeOutputKey": transcribe_output_key,
        "PollyOutputKey": polly_output_key,
        "SourceLanguageCode": source_lang_code,
        "TargetLanguageCode": target_lang_code,
        "JobName": job_name,
        "VoiceId": voice_id,
    }

    if deploy:
        return execute_state_machine(sf_input, sf_name, True, sf_role)
    else:
        return execute_state_machine(sf_input, sf_name)


if __name__ == "__main__":
    execute_nlp_state_machine()