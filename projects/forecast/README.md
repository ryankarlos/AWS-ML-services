### AWS Forecast 

Illustrating the use of AWS Forecasts service using the Manning Dataset. This is part of the Fbprophet library example
dataset which is a time series of the Wikipedia page hits for Peyton Manning
https://peerj.com/preprints/3190/
https://facebook.github.io/prophet/docs/quick_start.html#python-api

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/forecast/manning_raw_data_plot.png" height=1000></img>


The notebook `AWS_Forecast.ipynb` uses the functions in the modules in this package to 
import data into S3, create an AWS forecast dataset and import data into it from S3, 
train a predictor and then forecast using the model. 


#### Data prep 

The functions in modules `prepare_data_for_s3.py` filter the existing dataset to
only include historical data for one year (2015) and then reformat the dataset
to have columns ("timestamp", "target_value","item_id") and values as expected by AWS Forecast api.
Finally we call the s3 put object to add to created S3 bucket.

Module `dataset_and_import_jobs.py` creates an AWS Forecast dataset group and dataset 
https://docs.aws.amazon.com/forecast/latest/dg/howitworks-datasets-groups.html
Here we only use target time series dataset type 

As per https://docs.aws.amazon.com/forecast/latest/dg/howitworks-datasets-groups.html, 

"The dataset group must include a target time series dataset. The target time series dataset includes the 
target attribute (item_id) and timestamp attribute, as well as any dimensions. 
Related time series and Item metadata is optional".

In this example, the itemid column has been created and set to arbitary value (1)
as all the items belong to the same group (i.e Manning's wikipedia hits)

For illustration purposes and to generate the task viz, ive used dask delayed, but the dataset
size certainly does not warrant the need for it. 

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/forecast/data_processing_workflow.png" height=1000></img>


```
DATASET_FREQUENCY = "D"
ts_schema ={
   "Attributes":[
      {
         "AttributeName":"timestamp",
         "AttributeType":"timestamp"
      },
      {
         "AttributeName":"target_value",
         "AttributeType":"float"
      },
      {
         "AttributeName":"item_id",
         "AttributeType":"string"
      }
   ]
}
PROJECT = 'manning_ts'
DATA_VERSION = 1
dataset_name = f"{PROJECT}_{DATA_VERSION}"
dataset_arn = create_dataset(dataset_name, DATASET_FREQUENCY, ts_schema)
dataset_group_arn = create_dataset_group_with_dataset(dataset_name, dataset_arn)
```

We then create an import job to import the time series dataset from s3 into AWS forecast dataset
so it is ready for training. After creating the import job - we can check for job status before 
progressing to the training step


```
bucket_name = 'aws-forecast-demo-examples'
key = "manning_ts_2015.csv"
ts_dataset_import_job_response = create_import_job(bucket_name, key, dataset_arn, role_arn)
dataset_import_job_arn=ts_dataset_import_job_response['DatasetImportJobArn']
check_job_status(dataset_import_job_arn, job_type="import_data")
```

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/forecast/manning-datasets.png" ></img>

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/forecast/manning-dashboard.png" ></img>


#### Model Training

Create a predictor (an Amazon Forecast model) that is trained using the target time series. 
You can use predictors to generate forecasts based on your time-series data.

As per https://docs.aws.amazon.com/forecast/latest/dg/howitworks-predictor.html, the following
paramters are passed into the custom functions for creating the predictor

* Dataset group (defined previously)
* Forecast frequency – The granularity of your forecasts (in this case daily).
* Forecast horizon – The number of time steps being forecasted (in this case,
  set this to 35 days)
  
This custom function calls the forecast.create_predictor method and sets the
AutoML parameter to `True`. 
However, this can also be upgraded to AutoPredictor as detailed in 
https://docs.aws.amazon.com/forecast/latest/dg/howitworks-predictor.html
and is suggested as the preferred method by AWS

"
AutoPredictor is the default and preferred method to create a predictor with Amazon Forecast. AutoPredictor creates predictors by applying the optimal combination of algorithms for each time series in your dataset.
Predictors created with AutoPredictor are generally more accurate than predictors created with AutoML or manual selection."
"

```

FORECAST_LENGTH = 35
DATASET_FREQUENCY = "D"
predictor_name = f"{PROJECT}_{DATA_VERSION}_automl"
create_predictor_response , predictor_arn = train_aws_forecast_model(predictor_name, FORECAST_LENGTH, DATASET_FREQUENCY, dataset_group_arn)
check_job_status(predictor_arn, job_type="training")
```


### Backtest results

Amazon Forecast provides following metrics to evaluate predictors.
Quoting the following from AWS docs 
https://docs.aws.amazon.com/forecast/latest/dg/metrics.html

""
* Root Mean Square Error (RMSE): square root of the average of squared errors, and is therefore more sensitive to 
  outliers than other accuracy metrics. A lower value indicates a more accurate model.
  
* Weighted Quantile Loss (wQL): measures the accuracy of a model at a specified quantile. It is particularly useful 
  when there are different costs for underpredicting and overpredicting. By setting the weight (τ) of the wQL function, 
  you can automatically incorporate differing penalties for underpredicting and overpredicting.
  By default, Forecast computes wQL at 0.1 (P10), 0.5 (P50), and 0.9 (P90).

* Average Weighted Quantile Loss (Average wQL): mean value of weighted quantile losses over all specified quantiles. 
  By default, this will be the average of wQL[0.10], wQL[0.50], and wQL[0.90] 
  
* Mean Absolute Scaled Error (MASE): calculated by dividing the average error by a scaling factor. This scaling factor 
  is dependent on the seasonality value, m, which is selected based on the forecast frequency. A lower value indicates 
  a more accurate model. MASE is ideal for datasets that are cyclical in nature or have seasonal properties. 
  For example, forecasting for items that are in high demand during summers and in low demand during winters can 
  benefit from taking into account the seasonal impact.
  
* Mean Absolute Percentage Error (MAPE): takes the absolute value of the percentage error between observed and 
  predicted values for each unit of time, then averages those values. A lower value indicates a more accurate model.
  MAPE is useful for cases where values differ significantly between time points and outliers have a significant impact.
  
* Weighted Absolute Percentage Error (WAPE): measures the overall deviation of forecasted values from observed values. 
  WAPE is calculated by taking the sum of observed values and the sum of predicted values, and calculating the error 
  between those two values. A lower value indicates a more accurate model. WAPE is more robust to outliers than 
  Root Mean Square Error (RMSE) because it uses the absolute error instead of the squared error.
""


The metrics are provided for each backtest window 
specified. Quoting the following from AWS doc
https://docs.aws.amazon.com/forecast/latest/dg/metrics.html

""
Forecast uses backtesting to calculate accuracy metrics. If you run multiple backtests, Forecast averages each 
metric over all backtest windows. By default, Forecast computes one backtest, with the size of the backtest window 
(testing set) equal to the length of the forecast horizon (prediction window). You can set both the backtest window 
length and the number of backtest scenarios when training a predictor.
Forecast omits filled values from the backtesting process, and any item with filled values within a given 
backtest window will be excluded from that backtest. This is because Forecast only compares forecasted values with 
observed values during backtesting, and filled values are not observed values.
The backtest window must be at least as large as the forecast horizon, and smaller than half the length of the entire 
target time-series dataset. You can choose from between 1 and 5 backtests.
""

```
error_metrics = evaluate_backtesting_metrics(predictor_arn)
```

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/forecast/manning-predictors.png" ></img>


and to plot the backtest results for all metrics except 
Weighted Quantile Losses.

Looking at the results, seems like NPTS is the winning algorithm
followed by Deep AR Plus. 
So AWS Forecast, will use the NPTS model for serving forecasts

We can also see MASE metric better highlights the difference in
performance between various algorithms as it is more suited to
this dataset due to cyclical/seasonal properties in data

```
plot_backtest_metrics(error_metrics)
```

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/forecast/manning-backtest-results-plot.png" ></img>


#### Forecast and query

Now we have a trained model so we can create a forecast. This
includes predictions for every item (item_id) in the dataset group 
that was used to train the predictor. 
https://docs.aws.amazon.com/forecast/latest/dg/howitworks-forecast.html

```
forecast_name = f"{PROJECT}_{DATA_VERSION}_automl_forecast"
forecast_arn = create_forecast(forecast_name, predictor_arn)
```

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/forecast/manning-forecasts.png" ></img>


Once this is done, we can then query the forecast by passing a filter (key-value pair),
where the key/values are one of the schema attribute names and valid values respectively. 
This will return forecast for only those items that satisfy the criteria
https://docs.aws.amazon.com/forecast/latest/dg/howitworks-forecast.html
In this case, we query the forecast and return all the items 
by using the item id dimension

```
filters = {"item_id":"1"}
forecast_response = run_forecast_query_and_plot(forecast_arn, filters)
df = create_forecast_plot(forecast_response)

```

<img src="https://github.com/ryankarlos/AWS-ML-services/blob/master/screenshots/forecast/manning-forecast-p10-p50-p90-plot.png" ></img>


#### Terminating resources

Finally we can tear down all the AWS Forecast resources: predictor, forecast and 
dataset group 

```
kwargs = {'forecast':forecast_name,
'predictor':predictor_name
}
delete_training_forecast_resources(**kwargs)
```
