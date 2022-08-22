# High Level AWS ML services

AWS has a number of machine learning and artificial intelligence services and products that can be used in 
conjunction with each other to make smart applications.  Here, I will demonstrate practically how one can 
create ane end to end workflow involving some of these ML services, starting from raw labelled datasets to generating 
predictions for unseen data from deployed trained models. Click on the links for the services for working through 
the practical example workflow. This doc can be accessed either via [Github Pages](https://ryankarlos.github.io/AWS-ML-services/) or [Github Readme](https://github.com/ryankarlos/AWS-ML-services#readme).
Please refer to the github repo link at the top for all the scripts referenced in the examples.

* Use of multiple [AWS NLP Services](projects/nlp) including Comprehend, Transcribe, Translate and Polly for an application to translate speech into multiple languages.
* [AWS Forecast](projects/forecast) for forecasting the daily log-scale page views of an American Football Quarterback's Wikipedia page.
* [AWS Fraud Detector](projects/fraud) for classifying fraudulent online registered accounts for simulated data from Kaggle.
* [AWS Personalize](projects/personalize) for recommending new movies to users, based on their ratings to other similar movies.
* [AWS Rekognition](projects/rekognition)  for classifying food images into their respective categories 

For each of the examples, you would need to have a virtual environment setup if you need to run the scripts locally. Thsi can be setup 
by following the instructions in the next section.

## Environment and dependencies

We will use [pipenv](https://pipenv.pypa.io/en/latest/install/#installing-packages-for-your-project) to manage environment and dependencies
First install *pipenv* using *pip* command

```shell
pip install --user pipenv
```

Then create a virtual environment based on dependencies in *pipfile.lock* and *pipfile* in the base of the [Github repository](https://github.com/ryankarlos/AWS-ML-services)

```shell
$ pipenv shell     
```

To update the lock file if the pipefile is updated (for example, if you  have updated the dev-packages section), run:

```shell
$ pipenv update
```
This will also install the dependencies to the env. To install directly from lock file, can run `pipenv install` or `pipenv install -d` to
install specifically dev-packages

```shell
$ pipenv install -d

Installing dependencies from Pipfile.lock (595137)...
  🐍   ▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉ 43/43 — 00:00:17

```

To see a graph of packages and their dependencies, use the following command.

```shell
$ pipenv graph 
```
