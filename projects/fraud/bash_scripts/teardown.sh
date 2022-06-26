#!/bin/bash

resource=$1


variables=( "trans_num" "amt" "city_pop" "street" "job" "cc_num" "gender" "merchant" "last" "category" "zip" "city" "state" "first")
labels=("legit" "fraud")
rules=("investigate" "review" "approve")
outcomes=("high_risk" "low_risk" "medium_risk")
event_type="credit_card_transaction"
entity_type="customer"
detector_name="fraud_detector_demo"
model_name=fraud_model


if [[ $resource == "endpoint" ]]; then
    echo "Deleting endpoint"
    echo ""
    aws cloudformation delete-stack --stack-name GlueEndpointDev
elif [[ $resource == "detector" ]]; then
    echo ""
    echo "Delete model versions"
    aws frauddetector  delete-model-version --model-id $model_name --model-type ONLINE_FRAUD_INSIGHTS --model-version-number 1.0
    aws frauddetector  delete-model-version --model-id $model_name --model-type ONLINE_FRAUD_INSIGHTS --model-version-number 2.0


    echo ""
    echo "Delete model"
    aws frauddetector  delete-model --model-id $model_name --model-type ONLINE_FRAUD_INSIGHTS

    echo ""
    echo "Deleting detector version id 1"
    aws frauddetector delete-detector-version --detector-id $detector_name --detector-version-id 1


    echo ""
    for var in "${rules[@]}";
    do
        echo "Deleting rule $var"
        aws frauddetector  delete-rule --rule detectorId=$detector_name,ruleId=$var,ruleVersion=1
    done;


    echo ""
    echo "Deleting detector id $detector_name"
    aws frauddetector delete-detector --detector-id $detector_name

    echo ""
    echo "Deleting event-type $event_type"
    aws frauddetector delete-event-type --name $event_type

    echo ""
    echo "Deleting entity-type $entity_type"
    aws frauddetector delete-entity-type --name $entity_type

    echo ""
    for var in "${variables[@]}";
    do
        echo "Deleting variable $var"
        aws frauddetector  delete-variable --name $var
    done;


    echo ""
    for var in "${labels[@]}";
    do
        echo "Deleting label $var"
        aws frauddetector  delete-label --name $var
    done;

    echo ""
    for var in "${outcomes[@]}";
    do
        echo "Deleting outcome $var"
        aws frauddetector  delete-outcome --name $var
    done;


    echo ""
    echo "Deleting cloud formation stack"
    aws cloudformation delete-stack --stack-name FraudDetectorGlue
fi;