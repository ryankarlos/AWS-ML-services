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
        <h3><strong>Risk Score (out of 1000): </strong><span style="color: #ff9900;">{{ task.input.score.sample_fraud_detection_insightscore }}</span></h3>
        <hr>
        <h3> Claim Details </h3>
        <p style="padding-left: 50px;"><strong>Email Address   :  </strong>{{ task.input.taskObject.email_address }}</p>
        <p style="padding-left: 50px;"><strong>Billing Address :  </strong>{{ task.input.taskObject.billing_address }}</p>
        <p style="padding-left: 50px;"><strong>Billing State   :  </strong>{{ task.input.taskObject.billing_state }}</p>
        <p style="padding-left: 50px;"><strong>Billing Zip     :  </strong>{{ task.input.taskObject.billing_postal }}</p>
        <p style="padding-left: 50px;"><strong>Originating IP  :  </strong>{{ task.input.taskObject.ip_address }}</p>
        <p style="padding-left: 50px;"><strong>Phone Number    :  </strong>{{ task.input.taskObject.phone_number }}</p>
        <p style="padding-left: 50px;"><strong>User Agent      :  </strong>{{ task.input.taskObject.user_agent }}</p>
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
