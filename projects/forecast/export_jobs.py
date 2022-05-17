from common import forecast


def create_export_jobs(s3_export_path, role_arn, **kwargs):
    predictor_export = {}
    forecast_export = {}
    explain_export = {}

    if kwargs.get("predictor"):
        predictor_export = forecast.create_predictor_backtest_export_job(
            PredictorBacktestExportJobName=kwargs["predictor"]["name"],
            PredictorArn=kwargs["predictor"]["arn"],
            Destination={
                "S3Config": {
                    "Path": s3_export_path,
                    "RoleArn": role_arn,
                }
            },
        )

    if kwargs.get("forecast"):
        forecast_export = forecast.create_forecast_export_job(
            ForecastExportJobName=kwargs["forecast"]["name"],
            ForecastArn=kwargs["forecast"]["arn"],
            Destination={
                "S3Config": {
                    "Path": s3_export_path,
                    "RoleArn": role_arn,
                }
            },
        )

    if kwargs.get("explainability"):
        explain_export = forecast.create_explainability_export(
            ExplainabilityExportName=kwargs["explain"]["name"],
            ExplainabilityArn=kwargs["explain"]["arn"],
            Destination={"S3Config": {"Path": s3_export_path, "RoleArn": role_arn}},
        )
    return predictor_export, forecast_export, explain_export
