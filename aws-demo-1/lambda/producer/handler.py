import os
import json
import random
import datetime
import boto3
from kafka import KafkaProducer
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

DEVICES = [f"modem-{str(i).zfill(3)}" for i in range(1, 21)]
STATUSES = ["connected", "connected", "connected", "degraded", "disconnected"]


def get_bootstrap_servers():
    client = boto3.client('kafka', region_name=os.environ['AWS_REGION'])
    response = client.get_bootstrap_brokers(ClusterArn=os.environ['CLUSTER_ARN'])
    return response['BootstrapBrokerStringSaslIam']


def make_token(*args, **kwargs):
    token, _ = MSKAuthTokenProvider.generate_auth_token(os.environ['AWS_REGION'])
    return token, 0


def generate_record(device_id):
    return {
        "device_id": device_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "cpu_usage": round(random.uniform(5.0, 95.0), 2),
        "memory_usage": round(random.uniform(20.0, 90.0), 2),
        "connection_status": random.choice(STATUSES),
        "download_mbps": round(random.uniform(10.0, 300.0), 2),
        "upload_mbps": round(random.uniform(5.0, 100.0), 2),
        "signal_dbm": random.randint(-90, -45),
    }


def handler(event, context):
    brokers = get_bootstrap_servers()
    producer = KafkaProducer(
        bootstrap_servers=brokers,
        security_protocol='SASL_SSL',
        sasl_mechanism='OAUTHBEARER',
        sasl_oauth_token_provider=type('T', (), {'token': staticmethod(make_token)})(),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )
    topic = os.environ['TOPIC_NAME']
    devices = random.sample(DEVICES, 10)
    for device_id in devices:
        record = generate_record(device_id)
        producer.send(topic, value=record)
        print(f"Sent: {record}")
    producer.flush()
    producer.close()
    return {"statusCode": 200, "records_sent": 10}
