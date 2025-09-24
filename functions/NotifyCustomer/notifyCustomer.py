# **NOTE:** We're going to write a simple log of notification.
# In a real world example this could use AWS SNS to correctly distribute
# the notification.

def lambda_handler(event, context):
    notification = {
        'email': event['message']['customerEmail'],
        'orderId': event['order_id'] if event['available'] else None,
        'message': f"Order {event['order_id']} was placed successfully." if event['available'] 
                  else "Unfortunately we weren't able to place your order."
    }
    
    return notification