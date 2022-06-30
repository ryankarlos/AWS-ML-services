## Diagrams as Code

Diagrams lets you draw the cloud system architecture in Python code. This is very beneficial especially if 
one requires to keep track of changes to the architecture over time  via version control.
https://github.com/mingrammer/diagrams

#### Installation 

Diagrams required graphviz to render the diagrams so we need to install graphviz (https://graphviz.gitlab.io/download/) 
first.
https://diagrams.mingrammer.com/docs/getting-started/installation

For Windows, download and run the executable `graphviz-4.0.0 (64-bit) EXE installer [sha256]` 
 * Add Graphviz to system path
 * Select destination folder to install the packages and install

Check the system environment variables to confirm that `C:\Program Files\Graphviz\bin\` is added to the path variable.
or run `echo $PATH` is shell to check this.
Once graphviz is installed successfully we need to install diagrams by using below command which completes our installation.
If using pipenv, this is added to the pipfile and can be added to virtual env `pipenv update`. Otherwise, can 
run `pip install diagrams` inside your virtual env. 


#### Generating AWS Architecture diagrams

We can then run the script from the command line e.g.

``
$ python screenshots/aws_diagrams/fraud_train.py 
``

This should create a Diagram.png file in the directory from where the script was run. If we are in the root of the repo
and ran the command above, then the output file would be generated in the root of the repo. 

The script creates a diagram context object with the Diagram class. This constructor takes in a number of arguments 
e.g. first parameter is the filename ("Diagram"). There are other optional args to set the format of the file (default is png)
and whether to show the diagram as a pop up window when the script finishes running (show parameter - this is set to True but can be 
changed to false to stop this behaviour) 

More details can be found in the diagrams documentation https://diagrams.mingrammer.com/docs/guides/diagram

For more information on what different bits of the syntax do, please refer to these examples https://diagrams.mingrammer.com/docs/getting-started/examples