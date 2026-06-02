# aws-demo-1 — Serverless IoT Streaming Pipeline

End-to-end real-time data pipeline: EventBridge Scheduler → Lambda Producer → MSK Serverless (Kafka) → Lambda Consumer / Kinesis Firehose → DynamoDB / S3.

## Architecture

```
EventBridge Scheduler (every 1 min)
        │
        ▼
Lambda: Producer          (generates 10 synthetic modem telemetry records)
        │
        ▼
MSK Serverless ──────────────────────────┐
topic: modem-telemetry                   │
        │ Event Source Mapping           │ MSK Source
        ▼                                ▼
Lambda: Consumer              Kinesis Data Firehose
(writes latest device state)   (partitioned by date → S3)
        │                                │
        ▼                                ▼
DynamoDB: device-status          S3: data lake
```

## Lambda Functions

| Directory | Function | Purpose |
|-----------|----------|---------|
| `lambda/producer/` | `handler.py` | Publishes 10 synthetic modem records to Kafka |
| `lambda/consumer/` | `handler.py` | Reads from Kafka, upserts device state to DynamoDB |
| `lambda/topic_creator/` | `handler.py` | CloudFormation custom resource — creates Kafka topic at deploy time |
| `lambda/s3_cleanup/` | `handler.py` | CloudFormation custom resource — empties S3 bucket at teardown |

All functions use **Python 3.12**.

## Infrastructure

Plain **CloudFormation** (`template.yaml`) — no SAM transform.

Key resources:
- `AWS::MSK::ServerlessCluster` — IAM auth, placed in two private subnets
- `AWS::Lambda::EventSourceMapping` — Kafka → Consumer (TRIM_HORIZON)
- `AWS::KinesisFirehose::DeliveryStream` — MSKAsSource, S3 prefix partitioned by date
- `AWS::Scheduler::Schedule` — `rate(1 minute)` → Producer
- `AWS::DynamoDB::Table` — `device-status`, on-demand billing
- VPC with public subnet + NAT Gateway so Lambda in private subnets can reach the internet

## Deploy / Teardown

```bash
# Deploy (preferred — validates PROFILE)
make deploy PROFILE=<aws-profile>

# Teardown
make teardown PROFILE=<aws-profile>

# Direct scripts (STACK defaults to aws-demo-1, REGION to eu-west-1)
./scripts/deploy.sh <stack-name> <region>
./scripts/teardown.sh <stack-name> <region>
```

`deploy.sh` creates a temporary S3 bucket, packages each Lambda with its `pip` dependencies, then runs `aws cloudformation deploy`. Stack takes **8–12 minutes** to provision MSK.

`teardown.sh` deletes the stack (triggering the S3 cleanup custom resource) and removes the packaging bucket. All resources are fully removed.

## Known Constraints

- MSK Serverless is only available in select regions (`us-east-1`, `us-west-2`, `eu-west-1`, `eu-central-1`, `ap-southeast-1`, and a few others).
- The `ArtifactsBucket` CloudFormation parameter is injected automatically by `deploy.sh` — do not set it manually.
- Firehose uses `PRIVATE` connectivity, requiring the MSK security group to allow ingress on port 9098 from the Lambda SG.
