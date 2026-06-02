import os
import json
import base64
import boto3

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    records_written = 0

    for partition_key, records in event.get('records', {}).items():
        for record in records:
            payload = json.loads(base64.b64decode(record['value']).decode('utf-8'))
            table.put_item(Item={
                'device_id': payload['device_id'],
                'timestamp': payload['timestamp'],
                'cpu_usage': str(payload['cpu_usage']),
                'memory_usage': str(payload['memory_usage']),
                'connection_status': payload['connection_status'],
                'download_mbps': str(payload['download_mbps']),
                'upload_mbps': str(payload['upload_mbps']),
                'signal_dbm': payload['signal_dbm'],
            })
            records_written += 1

    print(f"Written {records_written} records to DynamoDB")
    return {"records_written": records_written}
