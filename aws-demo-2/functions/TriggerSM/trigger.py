import json
import os
import boto3

def lambda_handler(event, context):
    # Create Step Functions client
    stepfunctions = boto3.client('stepfunctions')
    
    # Set up parameters
    params = {
        'stateMachineArn': os.environ['SM_ARN'],
        'input': json.dumps(event)
    }
    
    try:
        # Start execution
        response = stepfunctions.start_execution(**params)
        return response
    except Exception as err:
        # Handle errors
        raise err