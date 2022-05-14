import pandas as pd
from pathlib import Path
import json
import itertools
from common import forecast, forecastquery
import numpy as np


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


def run_forecast_query(forecast_arn, filters):
    forecastResponse = forecastquery.query_forecast(
        ForecastArn=forecast_arn, Filters=filters
    )
    return forecastResponse


def create_forecast_plot(forecast_response):
    ts = {}

    timestamp = [k["Timestamp"] for k in forecast_response["p10"]]
    p10 = [k["Value"] for k in forecast_response["p10"]]
    p50 = [k["Value"] for k in forecast_response["p50"]]
    p90 = [k["Value"] for k in forecast_response["p90"]]

    ts["timestamp"] = timestamp
    ts["p10"] = p10
    ts["p50"] = p50
    ts["p90"] = p90
    df = pd.DataFrame(ts)
    df.plot(x="timestamp", figsize=(15, 8))
    return df


def plot_backtest_metrics(error_metrics):
    parsed_json = {
        "Algorithm": [],
        "WQuantLosses": [],
        "WAPE": [],
        "RMSE": [],
        "MASE": [],
        "MAPE": [],
        "AvgWQuantLoss": [],
    }
    for v in error_metrics:
        algo = v["AlgorithmArn"].split("/")[-1]
        weighted_quantile_losses = v["TestWindows"][0]["Metrics"][
            "WeightedQuantileLosses"
        ]
        wape = v["TestWindows"][0]["Metrics"]["ErrorMetrics"][0]["WAPE"]
        rmse = v["TestWindows"][0]["Metrics"]["ErrorMetrics"][0]["RMSE"]
        mase = v["TestWindows"][0]["Metrics"]["ErrorMetrics"][0]["MASE"]
        mape = v["TestWindows"][0]["Metrics"]["ErrorMetrics"][0]["MAPE"]
        avg_weighted_quantile_losses = v["TestWindows"][0]["Metrics"][
            "AverageWeightedQuantileLoss"
        ]
        parsed_json["Algorithm"].append(algo)
        parsed_json["WQuantLosses"].append(json.dumps(weighted_quantile_losses))
        parsed_json["WAPE"].append(np.round(wape, 4))
        parsed_json["RMSE"].append(np.round(rmse, 4))
        parsed_json["MASE"].append(np.round(mase, 4))
        parsed_json["MAPE"].append(np.round(mape, 4))
        parsed_json["AvgWQuantLoss"].append(np.round(avg_weighted_quantile_losses, 4))
    df = (
        pd.DataFrame(parsed_json)
        .set_index("Algorithm")
        .T.rename_axis("Metric", axis=0)
        .rename_axis(None, axis=1)
        .reset_index()
    )
    df.iloc[1::, :].plot(x="Metric", kind="bar", figsize=(15, 8), legend=True)
    return df


def save_results(basepath, *args):
    for output in args:
        results_path = str(Path(basepath).parents[0].joinpath("results", output[0]))
        print(f"saving to {output[0]}")
        with open(results_path, "w") as f:
            # set to default to str to convert datetime objects not serialisable to str
            json.dump(output[1], f, indent=4, default=str)
