#!/bin/bash

# Configuration
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::your-account-id:role/your-lambda-role" # User needs to replace this
FUNCTIONS=("function_a" "function_b" "function_c" "function_d")
MEMORIES=("512" "1024" "256" "512")

# Create a deployment package
mkdir -p build
cp common/utils.py build/

for i in "${!FUNCTIONS[@]}"; do
    FUNC_NAME=${FUNCTIONS[$i]}
    MEMORY=${MEMORIES[$i]}
    echo "Deploying $FUNC_NAME..."
    
    cp $FUNC_NAME/lambda_handler.py build/
    cd build
    zip -r ../$FUNC_NAME.zip .
    cd ..
    
    # Check if function exists
    aws lambda get-function --function-name $FUNC_NAME --region $REGION > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "Updating $FUNC_NAME..."
        aws lambda update-function-code --function-name $FUNC_NAME --zip-file fileb://$FUNC_NAME.zip --region $REGION
        aws lambda update-function-configuration --function-name $FUNC_NAME --memory-size $MEMORY --region $REGION
    else
        echo "Creating $FUNC_NAME..."
        aws lambda create-function --function-name $FUNC_NAME \
            --runtime python3.9 \
            --role $ROLE_ARN \
            --handler lambda_handler.lambda_handler \
            --zip-file fileb://$FUNC_NAME.zip \
            --memory-size $MEMORY \
            --region $REGION
    fi
    
    rm build/lambda_handler.py
    rm $FUNC_NAME.zip
done

rm -rf build
echo "Done."
