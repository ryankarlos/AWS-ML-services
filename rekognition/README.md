
All the scripts in this folder using AWS SDK for python can be found in the official docs https://docs.aws.amazon.com/rekognition/latest/customlabels-dg/what-is.html
Some of these scripts have been adapted and tailored for the use of these sample datasets.

#### Creating project

https://docs.aws.amazon.com/rekognition/latest/customlabels-dg/mp-create-project.html

```
$ python rekognition/creating_project.py custom_labels
INFO: Found credentials in shared credentials file: ~/.aws/credentials
INFO: Creating project: custom_labels
Creating project: custom_labels
Finished creating project: custom_labels
ARN: arn:aws:rekognition:us-east-1:376337229415:project/custom_labels/1647472407175
```

#### Creating dataset

https://docs.aws.amazon.com/rekognition/latest/customlabels-dg/md-create-dataset-existing-dataset-sdk.html





### Run inference


project_arn='arn:aws:rekognition:us-east-1:376337229415:project/custom_labels/1647472407175'
    model_arn='arn:aws:rekognition:us-east-1:376337229415:project/custom_labels/version/custom_labels.2022-03-17T02.28.09/1647484090427'
    min_inference_units=1 
    version_name='custom_labels.2022-03-17T02.28.09'


