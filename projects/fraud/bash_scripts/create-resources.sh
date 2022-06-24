#!/bin/bash


echo "Creating stack FraudDetectorGlue "
echo ""
aws cloudformation create-stack --stack-name FraudDetectorGlue \
--template-body file://cloudformation/fraud_detector.yaml \
--capabilities CAPABILITY_NAMED_IAM


