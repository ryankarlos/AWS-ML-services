import uuid
import time

fraud_template = """<script src="https://assets.crowd.aws/crowd-html-elements.js"></script>

<crowd-form>
      <crowd-classifier
          name="category"
          categories="['Fradulent, 'Valid, 'Needs further Review]"
          header="Select the most relevant category"
      >
      <classification-target>
        <h3><strong>Risk Score (out of 1000): </strong><span style="color: #ff9900;">{{ task.input.score.fraud_model_insightscore }}</span></h3>
        <hr>
        <h3> Claim Details </h3>
        <p style="padding-left: 50px;"><strong>Timestamp       :  </strong>{{ task.input.taskObject.EVENT_TIMESTAMP }}</p>
        <p style="padding-left: 50px;"><strong>Transaction No. :  </strong>{{ task.input.taskObject.variables.trans_num }}</p>
        <p style="padding-left: 50px;"><strong>Amount          :  </strong>{{ task.input.taskObject.variables.amt }}</p>
        <p style="padding-left: 50px;"><strong>Zip Code        :  </strong>{{ task.input.taskObject.variables.zip }}</p>
        <p style="padding-left: 50px;"><strong>City            :  </strong>{{ task.input.taskObject.variables.city }}</p>
        <p style="padding-left: 50px;"><strong>First Name      :  </strong>{{ task.input.taskObject.variables.first }}</p>
        <p style="padding-left: 50px;"><strong>Job Title       :  </strong>{{ task.input.taskObject.variables.job }}</p>
        <p style="padding-left: 50px;"><strong>Street          :  </strong>{{ task.input.taskObject.variables.street }}</p>
        <p style="padding-left: 50px;"><strong>Category        :  </strong>{{ task.input.taskObject.variables.category }}</p>
        <p style="padding-left: 50px;"><strong>City Population :  </strong>{{ task.input.taskObject.variables.city_pop }}</p>
        <p style="padding-left: 50px;"><strong>Gender          :  </strong>{{ task.input.taskObject.variables.gender }}</p>
        <p style="padding-left: 50px;"><strong>Credit Card No. :  </strong>{{ task.input.taskObject.variables.cc_num }}</p>
        <p style="padding-left: 50px;"><strong>Last Name       :  </strong>{{ task.input.taskObject.variables.last }}</p>
        <p style="padding-left: 50px;"><strong>State           :  </strong>{{ task.input.taskObject.variables.state }}</p>
        <p style="padding-left: 50px;"><strong>Merchant        :  </strong>{{ task.input.taskObject.variables.merchant }}</p>
      </classification-target>

      <full-instructions header="Claim Verification instructions">
      <ol>
        <li><strong>Review</strong> the claim application and documents carefully.</li>
        <li>Mark the claim as valid or fraudulent</li>
      </ol>
      </full-instructions>

      <short-instructions>
           Choose the most relevant category that is expressed by the text. 
      </short-instructions>
    </crowd-classifier>

</crowd-form>
"""

# Replace the following with your bucket name
uniqueId = str(int(round(time.time() * 1000)))
flowDefinitionName = f"fraud-detector-a2i-{uniqueId}"
humanLoopName = "Fraud-detector-" + str(int(round(time.time() * 1000)))
taskUIName = "fraud" + str(uuid.uuid1())
ROLE = "A2ISagemakerExecutionRole"
BUCKET = "s3://fraud-sample-data"
