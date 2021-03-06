drop schema if exists spectrum_manning;

create external schema spectrum_manning
from data catalog
database 'spectrumdb'
iam_role 'arn:aws:iam::376337229415:role/myspectrum_role'
create external database if not exists;

drop table IF EXISTS spectrum_manning.manning;

create external table spectrum_manning.manning  (item_id smallint, timestamp date, target_value float)
row format delimited
fields terminated by '\t'
stored as textfile
location 's3://aws-forecast-demo-examples/glue_prep_for_aws_forecast/';

SELECT COUNT(*)
FROM spectrum_manning.manning