import boto3
import cfnresponse

def handler(event, context):
    bucket_name = event['ResourceProperties']['BucketName']
    if event['RequestType'] == 'Delete':
        try:
            s3 = boto3.client('s3')
            paginator = s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                objects = [{'Key': obj['Key']} for obj in page.get('Contents', [])]
                if objects:
                    s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
        except Exception as e:
            print(f"Error emptying bucket: {e}")
            cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})
            return
    cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
