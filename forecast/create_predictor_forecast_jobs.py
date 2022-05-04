import pandas as pd
from pathlib import Path
import json
import itertools
from forecast.common import forecast, forecastquery


def train_aws_forecast_model(
    predictor_name, forecast_length, dataset_frequency, dataset_group_arn
):
    create_predictor_response = forecast.create_predictor(
        PredictorName=predictor_name,
        ForecastHorizon=forecast_length,
        PerformAutoML=True,
        InputDataConfig={"DatasetGroupArn": dataset_group_arn},
        FeaturizationConfig={"ForecastFrequency": dataset_frequency},
    )
    predictor_arn = create_predictor_response["PredictorArn"]
    return create_predictor_response, predictor_arn


def get_training_job_config_and_execution_details(predictor_arn):
    dict_predictor = forecast.describe_predictor(PredictorArn=predictor_arn)
    training_job_config = list(itertools.islice(dict_predictor.items(), 3, 11))
    return training_job_config, dict_predictor["PredictorExecutionDetails"]


def evaluate_backtesting_metrics(predictor_arn):
    # backtesting error metrics
    error_metrics = forecast.get_accuracy_metrics(PredictorArn=predictor_arn)
    print(error_metrics["PredictorEvaluationResults"])
    return error_metrics


def create_forecast(forecast_name, predictor_arn):
    create_forecast_response = forecast.create_forecast(
        ForecastName=forecast_name, PredictorArn=predictor_arn
    )
    forecast_arn = create_forecast_response["ForecastArn"]
    print(forecast_arn)
    return forecast_arn


def run_forecast_query_and_plot(forecast_arn, filters):
    forecastResponse = forecastquery.query_forecast(
        ForecastArn=forecast_arn, Filters=filters
    )
    # Generate DF
    prediction_df_p10 = pd.DataFrame.from_dict(
        forecastResponse["Forecast"]["Predictions"]["p10"]
    )
    prediction_df_p10.head()
    # Plot
    prediction_df_p10.plot()
    prediction_df_p50 = pd.DataFrame.from_dict(
        forecastResponse["Forecast"]["Predictions"]["p50"]
    )
    prediction_df_p50.plot()
    prediction_df_p90 = pd.DataFrame.from_dict(
        forecastResponse["Forecast"]["Predictions"]["p90"]
    )
    prediction_df_p90.plot()
    return prediction_df_p10, prediction_df_p50, prediction_df_p90


def save_results(basepath, *args):
    for output in args:
        results_path = str(Path(basepath).parents[0].joinpath("results", output[0]))
        print(f"saving to {output[0]}")
        with open(results_path, "w") as f:
            # set to default to str to convert datetime objects not serialisable to str
            json.dump(output[1], f, indent=4, default=str)
