import json
import os
import uuid
import boto3

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def lambda_handler(event, context):
    # Generate a unique order ID
    order_id = str(uuid.uuid4())
    
    # Get the DynamoDB table
    table = dynamodb.Table(os.environ['DDB_TABLE'])
    
    # Prepare the item to be inserted
    item = {
        'customer_id': event['message']['customerId'],
        'order_id': order_id,
        'item_name': event['message']['itemName']
    }
    
    # Prepare the response
    response = {
        'message': event['message'],
        'order_id': order_id,
        'available': event['available']
    }
    
    try:
        # Put item into DynamoDB
        db_response = table.put_item(
            Item=item,
            ReturnConsumedCapacity='TOTAL'
        )
        
        print(db_response)
        return response
        
    except Exception as err:
        print(err)
        raise err