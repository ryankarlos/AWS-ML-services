#!/bin/bash

resource=$1


if [[ $resource == "detector" ]]; then
  echo "Creating stack FraudDetectorGlue "
  echo ""
  aws cloudformation create-stack --stack-name FraudDetectorGlue \
  --template-body file://cloudformation/fraud_detector.yaml \
  --capabilities CAPABILITY_NAMED_IAM
elif [[ $resource == "endpoint" ]]; then
  echo "Creating stack glue dev endpoint "
  echo ""
  aws cloudformation create-stack --stack-name GlueEndpointDev \
  --template-body file://cloudformation/glue-dev-endpoint.yaml \
  --capabilities CAPABILITY_NAMED_IAM
else
  echo "arg should be either 'endpoint' or 'detector'. You passed in $1. Exiting scipt .."
fi;

