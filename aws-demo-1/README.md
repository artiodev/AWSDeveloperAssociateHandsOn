# Serverless IoT Streaming Pipeline on AWS

A fully serverless, end-to-end real-time data pipeline built on Amazon MSK Serverless and Apache Kafka.

Deployed with a **single CloudFormation stack** — one command to create everything, one to tear it all down.

## Architecture

```
EventBridge Scheduler (every 1 min)
         │
         ▼
  Lambda: Producer
  (10 synthetic IoT modem records per invocation)
         │
         ▼
  MSK Serverless  ──────────────────────────────┐
  topic: modem-telemetry                        │
         │                                      │
         │ Event Source Mapping                 │ MSK Source
         ▼                                      ▼
  Lambda: Consumer                    Kinesis Data Firehose
  (latest device state)                 (all events, partitioned)
         │                                      │
         ▼                                      ▼
  DynamoDB: device-status              S3: data lake
  (real-time queries)                  (historical analytics)
```

Each Kafka message is a JSON record representing a synthetic modem reading:

```json
{
  "device_id": "modem-007",
  "timestamp": "2024-01-15T10:30:00Z",
  "cpu_usage": 42.1,
  "memory_usage": 68.4,
  "connection_status": "connected",
  "download_mbps": 145.2,
  "upload_mbps": 52.8,
  "signal_dbm": -61
}
```

## AWS Services

| Service | Role |
|---------|------|
| Amazon MSK Serverless | Managed Apache Kafka — no broker management |
| AWS Lambda (×4) | Producer, Consumer, topic setup, S3 cleanup |
| Amazon Kinesis Data Firehose | MSK → S3 data lake ingestion |
| Amazon DynamoDB | Real-time device state store |
| Amazon S3 | Historical data lake |
| Amazon EventBridge Scheduler | Triggers producer every minute |
| AWS CloudFormation | Full infrastructure as code |

## Prerequisites

- AWS CLI configured (`aws configure`)
- Python 3.12+ and `pip` installed
- Permissions to create VPC, MSK, Lambda, DynamoDB, S3, Firehose, IAM roles

## Supported Regions

MSK Serverless is available in: `us-east-1`, `us-west-2`, `eu-west-1`, `eu-central-1`, `ap-southeast-1`, and others. Check [AWS MSK Serverless availability](https://docs.aws.amazon.com/msk/latest/developerguide/serverless.html).

## Deploy

```bash
./scripts/deploy.sh <stack-name> <region>
# Example:
./scripts/deploy.sh msk-iot-demo us-east-1
```

The script:
1. Creates a temporary S3 bucket for Lambda packaging
2. Packages each Lambda function with its dependencies
3. Deploys the CloudFormation stack (~8–12 minutes for MSK provisioning)

After deploy, the pipeline is live. The Producer Lambda fires every minute and you can query DynamoDB immediately:

```bash
aws dynamodb scan \
  --table-name <stack-name>-device-status \
  --region <region>
```

## Teardown

```bash
./scripts/teardown.sh <stack-name> <region>
```

This deletes the CloudFormation stack (which empties the S3 data lake via a cleanup Lambda) and removes the packaging bucket. **All resources are fully removed** — no leftover costs.

## What's Next

- Query the S3 data lake with **Amazon Athena** for historical analytics
- Add a **Glue Crawler** to auto-discover schema and convert JSON to Parquet
- Build a **CloudWatch dashboard** to visualize Lambda metrics and Firehose delivery
- Extend the schema with additional sensor types (temperature, GPS)
