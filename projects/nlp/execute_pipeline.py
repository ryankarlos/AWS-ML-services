from step_functions.state_machine_resource import execute_state_machine
import click


# as per available non english ids https://docs.aws.amazon.com/polly/latest/dg/ntts-voices-main.html
NEURAL_VOICE_LIST = [
    "Vicki",
    "Bianca",
    "Takumi",
    "Seoyeon",
    "Camila",
    "Vitoria",
    "Ines",
    "Lucia",
    "Mia",
    "Lupe",
    "Lea",
    "Gabrielle",
    "Hannah",
    "Arlet",
]

# note some of comprehend services like sentiment are less restrictive but detect syntax only allows these
COMPREHEND_LANG_CODES = [
    "de",
    "pt",
    "en",
    "it",
    "fr",
    "es",
]


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
    "--source_filename",
    default="transcribe-sample.mp3",
    help="filename of source mp3",
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
    source_filename,
    source_lang_code,
    job_name,
    voice_id,
    deploy,
    sf_role,
):

    if voice_id in NEURAL_VOICE_LIST:
        engine = "neural"
    else:
        engine = "standard"

    if target_lang_code in COMPREHEND_LANG_CODES:
        skip_comprehend = False
    else:
        skip_comprehend = True

    sf_input = {
        "BucketName": bucket,
        "Source": f"s3://{bucket}/source/{source_lang_code}/{source_filename}",
        "TranscribeOutputKey": f"transcribe/{target_lang_code}/transcribed.json",
        "PollyVideoOutputKey": f"polly/{target_lang_code}/{voice_id}/",
        "PollyResponseOutputKey": f"polly/{target_lang_code}/response.json",
        "ComprehendOutputKey": f"comprehend/{target_lang_code}/response.json",
        "SourceLanguageCode": source_lang_code,
        "TargetLanguageCode": target_lang_code,
        "JobName": job_name,
        "VoiceId": voice_id,
        "EngineType": engine,
        "SkipComprehend": skip_comprehend,
    }

    if deploy:
        return execute_state_machine(sf_input, sf_name, True, sf_role)
    else:
        return execute_state_machine(sf_input, sf_name)


if __name__ == "__main__":
    execute_nlp_state_machine()
