#!/bin/bash

# Configuration
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::953334886326:role/domino-lambda-role"

# Exp 1 Functions
EXP1_FUNCS=("function_a" "function_b" "function_c" "function_d")
EXP1_MEMS=("512" "1024" "256" "512")

# Exp 2 Functions
EXP2_FUNCS=("v_a" "v_b" "v_c" "i_a" "i_b" "i_c" "i_d" "e_a" "e_b" "e_c" "e_d")
EXP2_MEMS=("512" "1024" "512" "512" "1024" "1024" "512" "512" "512" "512" "512")

deploy_group() {
    local group_name=$1
    local -a funcs=("${!2}")
    local -a mems=("${!3}")
    local handler_path=$4

    mkdir -p build
    cp common/utils.py build/
    cp "$handler_path" build/lambda_handler.py

    for i in "${!funcs[@]}"; do
        FUNC_NAME=${funcs[$i]}
        MEMORY=${mems[$i]}
        echo "Deploying $FUNC_NAME ($MEMORY MB)..."
        
        cd build
        zip -r ../$FUNC_NAME.zip . > /dev/null
        cd ..
        
        aws lambda get-function --function-name $FUNC_NAME --region $REGION > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo "Updating $FUNC_NAME..."
            aws lambda update-function-code --function-name $FUNC_NAME --zip-file fileb://$FUNC_NAME.zip --region $REGION > /dev/null
            echo "Waiting for $FUNC_NAME to finish updating..."
            aws lambda wait function-updated --function-name $FUNC_NAME --region $REGION
            aws lambda update-function-configuration --function-name $FUNC_NAME --memory-size $MEMORY --timeout 10 --region $REGION > /dev/null
        else
            echo "Creating $FUNC_NAME..."
            aws lambda create-function --function-name $FUNC_NAME \
                --runtime python3.9 \
                --role $ROLE_ARN \
                --handler lambda_handler.lambda_handler \
                --zip-file fileb://$FUNC_NAME.zip \
                --memory-size $MEMORY \
                --timeout 10 \
                --region $REGION > /dev/null
            aws lambda wait function-active --function-name $FUNC_NAME --region $REGION
        fi
        rm $FUNC_NAME.zip
    done
    rm -rf build
}

# Deploy Exp 1
echo "--- Deploying Experiment 1 Functions ---"
deploy_group "exp1" EXP1_FUNCS[@] EXP1_MEMS[@] "function_a/lambda_handler.py" # Any exp1 handler works as they are similar now

# Deploy Exp 2
echo "--- Deploying Experiment 2 Functions ---"
deploy_group "exp2" EXP2_FUNCS[@] EXP2_MEMS[@] "exp2/generic_handler.py"

echo "All deployments done."
