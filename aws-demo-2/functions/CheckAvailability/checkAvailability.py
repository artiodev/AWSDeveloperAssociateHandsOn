import json

def lambda_handler(event, context):
    # Parse the message from SQS record
    message = json.loads(event['Records'][0]['body'])
    
    # Obviously it's an example, everyone knows that there aren't graphics cards available
    available_item_name = "Nvidia RTX 3070"
    
    # Check if the item is available
    available = (message['itemName'] == available_item_name)
    
    response = {
        'message': message,
        'available': available
    }
    
    return response