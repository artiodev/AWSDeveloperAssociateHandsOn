# Serverless Order Processing with Step Functions

A fully serverless order workflow built on AWS Step Functions, Lambda, SQS, and DynamoDB. An incoming order message triggers a state machine that checks item availability, places the order, and notifies the customer — all coordinated without custom orchestration code.

## Architecture

```
SQS: PlaceOrderQueue
        │  (BatchSize: 1)
        ▼
Lambda: TriggerSM
        │  starts execution
        ▼
Step Functions: place-order (STANDARD)
        │
        ├─► CheckAvailability ──► ValidateAvailability (Choice)
        │                               │              │
        │                          available?     not available?
        │                               │              │
        │                               ▼              ▼
        │                          PlaceOrder    NotifyCustomer ──► END
        │                               │
        └───────────────────────────────▼
                                  NotifyCustomer ──► END
```

### State machine flow

1. **CheckAvailability** — checks whether the requested item is in stock
2. **ValidateAvailability** — Choice state: branches on `$.available`
3. **PlaceOrder** — writes the order to DynamoDB, generates a UUID `order_id`
4. **NotifyCustomer** — logs notification with order status (available or not)

## AWS Services

| Service | Role |
|---------|------|
| Amazon SQS | Receives order requests; triggers TriggerSM |
| AWS Step Functions (STANDARD) | Orchestrates the order workflow |
| AWS Lambda (×4) | TriggerSM, CheckAvailability, PlaceOrder, NotifyCustomer |
| Amazon DynamoDB | Persists placed orders (`orders-<env>`) |
| Amazon CloudWatch Logs | Full Step Functions execution logs |

## Input Message Format

Messages pushed to `PlaceOrderQueue` must be JSON:

```json
{
  "itemName": "Nvidia RTX 3070",
  "customerId": "customer-123",
  "customerEmail": "customer@example.com"
}
```

`CheckAvailability` currently hard-codes `"Nvidia RTX 3070"` as the only available item (it's a demo).

## Prerequisites

- AWS CLI configured (`aws configure`)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed
- Python 3.12+

## Deploy

```bash
sam build
sam deploy --guided   # first deploy — prompts for stack name, region, Environment
```

On subsequent deploys:

```bash
sam deploy
```

The `Environment` parameter (e.g. `dev`, `prod`) is appended to all resource names:
- `PlaceOrderQueue-dev`
- `orders-dev`
- `place-order-dev`

## Test

Send a test message to SQS to trigger a full execution:

```bash
aws sqs send-message \
  --queue-url <PlaceOrderQueue-URL> \
  --message-body '{"itemName":"Nvidia RTX 3070","customerId":"cust-001","customerEmail":"test@example.com"}' \
  --region <region>
```

Check the Step Functions console or query DynamoDB:

```bash
aws dynamodb scan \
  --table-name orders-<env> \
  --region <region>
```

## Teardown

```bash
aws cloudformation delete-stack --stack-name <stack-name> --region <region>
```

## What's Next

- Replace the `CheckAvailability` stub with a real inventory lookup (e.g. DynamoDB or an external API)
- Replace the `NotifyCustomer` log stub with **Amazon SNS** or **SES** for real email/SMS delivery
- Add an **Express** state machine variant for high-volume, low-latency orders
- Upgrade Lambda runtime from `nodejs12.x` (end-of-life) to `python3.12`
