## Trying out various Auto ML services on AWS 

* Rekognition
* Transcribe
* Translate
* Textract
* Forecast
* Comprehend
* Personalize
* Fraud Detector

### Environment and dependencies


Using pipenv  to manage environment and dependencies
https://pipenv.pypa.io/en/latest/install/#installing-packages-for-your-project

first install pipenv

```
pip install --user pipenv
```

Then create virtual env based on dependencies in pipfile.lock and pipfile

```
$ pipenv shell     
        
Creating a virtualenv for this project...
Pipfile: /Users/rk1103/Documents/AWS-ML-services/Pipfile
Using /Users/rk1103/opt/miniconda3/bin/python3.9 (3.9.1) to create virtualenv...
⠸ Creating virtual environment...created virtual environment CPython3.9.1.final.0-64 in 931ms
  creator CPython3Posix(dest=/Users/rk1103/.local/share/virtualenvs/AWS-ML-services-sGYPpasX, clear=False, no_vcs_ignore=False, global=False)
  seeder FromAppData(download=False, pip=bundle, setuptools=bundle, wheel=bundle, via=copy, app_data_dir=/Users/rk1103/Library/Application Support/virtualenv)
    added seed packages: pip==21.2.4, setuptools==58.1.0, wheel==0.37.0
  activators BashActivator,CShellActivator,FishActivator,PowerShellActivator,PythonActivator,XonshActivator

✔ Successfully created virtual environment! 
Virtualenv location: /Users/rk1103/.local/share/virtualenvs/AWS-ML-services-sGYPpasX
Launching subshell in virtual environment...
 . /Users/rk1103/.local/share/virtualenvs/AWS-ML-services-sGYPpasX/bin/activate

```

to update the lock file if the pipefile is updated, run:

```
$ pipenv update

Running $ pipenv lock then $ pipenv sync.
Locking [dev-packages] dependencies...
Locking [packages] dependencies...
Building requirements...
Resolving dependencies...
✔ Success! 
Updated Pipfile.lock (687a38)!
Installing dependencies from Pipfile.lock (687a38)...
  🐍   ▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉ 41/41 — 00:00:30
All dependencies are now up-to-date!

```

To see a graph of packages and their dependencies


```
$ pipenv graph 


awscli==1.23.5
  - botocore [required: ==1.25.5, installed: 1.25.5]
    - jmespath [required: >=0.7.1,<2.0.0, installed: 1.0.0]
    - python-dateutil [required: >=2.1,<3.0.0, installed: 2.8.2]
      - six [required: >=1.5, installed: 1.16.0]
    - urllib3 [required: >=1.25.4,<1.27, installed: 1.26.9]
  - colorama [required: >=0.2.5,<0.4.5, installed: 0.4.4]
  - docutils [required: >=0.10,<0.16, installed: 0.15.2]
  - PyYAML [required: >=3.10,<5.5, installed: 5.4.1]
  - rsa [required: >=3.1.2,<4.8, installed: 4.7.2]
    - pyasn1 [required: >=0.1.3, installed: 0.4.8]
  - s3transfer [required: >=0.5.0,<0.6.0, installed: 0.5.2]
    - botocore [required: >=1.12.36,<2.0a.0, installed: 1.25.5]
      - jmespath [required: >=0.7.1,<2.0.0, installed: 1.0.0]
      - python-dateutil [required: >=2.1,<3.0.0, installed: 2.8.2]
        - six [required: >=1.5, installed: 1.16.0]
      - urllib3 [required: >=1.25.4,<1.27, installed: 1.26.9]
black==22.3.0
  - click [required: >=8.0.0, installed: 8.1.3]
  - mypy-extensions [required: >=0.4.3, installed: 0.4.3]
  - pathspec [required: >=0.9.0, installed: 0.9.0]
  - platformdirs [required: >=2, installed: 2.5.2]
  - tomli [required: >=1.1.0, installed: 2.0.1]
  - typing-extensions [required: >=3.10.0.0, installed: 4.2.0]
boto==2.49.0
dask==2022.5.0
  - cloudpickle [required: >=1.1.1, installed: 2.0.0]
  - fsspec [required: >=0.6.0, installed: 2022.3.0]
  - packaging [required: >=20.0, installed: 21.3]
    - pyparsing [required: >=2.0.2,!=3.0.5, installed: 3.0.8]
  - partd [required: >=0.3.10, installed: 1.2.0]
    - locket [required: Any, installed: 1.0.0]
    - toolz [required: Any, installed: 0.11.2]
  - pyyaml [required: >=5.3.1, installed: 5.4.1]
  - toolz [required: >=0.8.2, installed: 0.11.2]
matplotlib==3.5.2
  - cycler [required: >=0.10, installed: 0.11.0]
  - fonttools [required: >=4.22.0, installed: 4.33.3]
  - kiwisolver [required: >=1.0.1, installed: 1.4.2]
  - numpy [required: >=1.17, installed: 1.22.3]
  - packaging [required: >=20.0, installed: 21.3]
    - pyparsing [required: >=2.0.2,!=3.0.5, installed: 3.0.8]
  - pillow [required: >=6.2.0, installed: 9.1.0]
  - pyparsing [required: >=2.2.1, installed: 3.0.8]
  - python-dateutil [required: >=2.7, installed: 2.8.2]
    - six [required: >=1.5, installed: 1.16.0]
pipenv==2022.1.8
  - certifi [required: Any, installed: 2021.10.8]
  - pip [required: >=18.0, installed: 21.2.4]
  - setuptools [required: >=36.2.1, installed: 58.1.0]
  - virtualenv [required: Any, installed: 20.14.1]
    - distlib [required: >=0.3.1,<1, installed: 0.3.4]
    - filelock [required: >=3.2,<4, installed: 3.6.0]
    - platformdirs [required: >=2,<3, installed: 2.5.2]
    - six [required: >=1.9.0,<2, installed: 1.16.0]
  - virtualenv-clone [required: >=0.2.5, installed: 0.5.7]
tqdm==4.64.0

```
