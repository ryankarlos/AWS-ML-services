from common import forecast


def delete_dataset_resources(dataset_name):
    # this assumes you have the same name for dataset and dataset import job
    group_list = forecast.list_dataset_groups()["DatasetGroups"]
    dataset_group_arn = [
        x["DatasetGroupArn"]
        for x in group_list
        if x["DatasetGroupName"] == dataset_name
    ]
    if dataset_group_arn:
        forecast.delete_dataset_group(DatasetGroupArn=dataset_group_arn[0])
        try:
            forecast.describe_dataset_group(DatasetGroupArn=dataset_group_arn)
        except forecast.exceptions.ResourceNotFoundException:
            print(f"Dataset group resource successfully deleted")

    else:
        print("No dataset group resource exists")

    dataset_list = forecast.list_datasets()["Datasets"]
    dataset_arn = [
        x["DatasetArn"] for x in dataset_list if x["DatasetName"] == dataset_name
    ]

    if dataset_arn:
        # first check if any dataset import job being referenced by dataset - then need to delete that first
        dataset_import_job_list = forecast.list_dataset_import_jobs()[
            "DatasetImportJobs"
        ]
        dataset_import_job_arn = [
            x["DatasetImportJobArn"]
            for x in dataset_import_job_list
            if x["DatasetImportJobName"] == dataset_name
        ]
        if dataset_import_job_arn:
            forecast.delete_dataset_import_job(
                DatasetImportJobArn=dataset_import_job_arn[0]
            )
        forecast.delete_dataset(DatasetArn=dataset_arn[0])
        print(forecast.describe_dataset(DatasetArn=dataset_arn))
        try:
            # This also confirms that respective import jobs are deleted as it depends on
            # dataset so it should have been deleted first before dataset resource can be deleted
            forecast.describe_dataset(DatasetArn=dataset_arn)
        except forecast.exceptions.ResourceNotFoundException:
            print(f"Dataset and import jobs successfully deleted")
    else:
        print("No dataset resource exists")


def delete_training_forecast_resources(auto_predictor=False,**kwargs):
    '''
    This will not work if resource is created from auto predictor action.
    :param auto_predictor:
    :param kwargs:
    :return:
    '''
    if "predictor" in kwargs.keys():
        pred_list = forecast.list_predictors()["Predictors"]
        if not pred_list:
            print("No predictor job currently exists")
        else:
            for i in pred_list:
                if i["PredictorName"] == kwargs["predictor"]:
                    predictor_arn = i["PredictorArn"]
                    print(f"Deleting {predictor_arn}")
                    forecast.delete_predictor(PredictorArn=predictor_arn)
                    try:
                        # note by checking just predicotr resource being deleted, we can
                        # confirm that respective forecast resource does not exist as it depends on
                        # predictor so it should have been deleted first otherwise error is thrown
                        forecast.describe_predictor(PredictorArn=predictor_arn)
                    except forecast.exceptions.ResourceNotFoundException:
                        print(f"Training and forecast job successfully deleted")
    if "forecast" in kwargs.keys():
        forecast_list = forecast.list_forecasts()["Forecasts"]
        if not forecast_list:
            print("No forecast job currently exists")
        else:
            for i in forecast_list:
                if i["ForecastName"] == kwargs["forecast"]:
                    forecast_arn = i["ForecastArn"]
                    print(f"Deleting {forecast_arn}")
                    forecast.delete_forecast(ForecastArn=forecast_arn)


def delete_explainability_resource(arn):
    print(f"Deleting explainability resource: {arn}")
    forecast.delete_explainability(ExplainabilityArn=arn)


def delete_export_jobs(**kwargs):
    if kwargs.get("explain_arn"):
        forecast.delete_explainability_export(ExplainabilityExportArn="string")
    if kwargs.get("forecast_arn"):
        forecast.delete_forecast_export_job(ForecastExportJobArn=kwargs["forecast_arn"])
    if kwargs.get("predictor_arn"):
        forecast.delete_predictor_backtest_export_job(
            PredictorBacktestExportJobArn=kwargs["predictor_arn"]
        )


def delete_resource_tree(arn):
    """
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/forecast.html#ForecastService.Client.delete_resource_tree
    Deletes an entire resource tree. This operation will
    delete the parent resource and its child resources.
    parent << child resource hierarchies: Dataset << Dataset Group << Predictor << Forecast
    e.g. in above predictor is parent and forecast is child

    """
    response = forecast.delete_resource_tree(
        ResourceArn=arn
    )
    return response