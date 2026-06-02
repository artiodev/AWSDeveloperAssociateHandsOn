import os
import json
import boto3
import cfnresponse
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

def get_bootstrap_servers(cluster_arn, region):
    client = boto3.client('kafka', region_name=region)
    response = client.get_bootstrap_brokers(ClusterArn=cluster_arn)
    return response['BootstrapBrokerStringSaslIam']

def handler(event, context):
    props = event['ResourceProperties']
    cluster_arn = props['ClusterArn']
    topic_name = props['TopicName']
    region = os.environ['AWS_REGION']

    if event['RequestType'] in ('Update', 'Delete'):
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return

    try:
        brokers = get_bootstrap_servers(cluster_arn, region)
        admin = KafkaAdminClient(
            bootstrap_servers=brokers,
            security_protocol='SASL_SSL',
            sasl_mechanism='OAUTHBEARER',
            sasl_oauth_token_provider=_token_provider(),
        )
        try:
            admin.create_topics([NewTopic(name=topic_name, num_partitions=4, replication_factor=3)])
        except TopicAlreadyExistsError:
            pass
        admin.close()
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {'TopicName': topic_name})
    except Exception as e:
        print(f"Error creating topic: {e}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})


def _token_provider():
    """MSK IAM OAuth token provider using AWS credentials."""
    import urllib.request
    import hmac, hashlib, datetime

    class MSKTokenProvider:
        def token(self):
            session = boto3.Session()
            creds = session.get_credentials().get_frozen_credentials()
            region = os.environ['AWS_REGION']
            # Use aws-msk-iam-sasl-signer-python if available, else generate manually
            try:
                from aws_msk_iam_sasl_signer import MSKAuthTokenProvider
                token, _ = MSKAuthTokenProvider.generate_auth_token(region)
                return token
            except ImportError:
                raise RuntimeError("aws-msk-iam-sasl-signer not available")

    return MSKTokenProvider()
