# aws-demo-2 — Order Processing with Step Functions

Serverless order workflow: SQS → TriggerSM Lambda → Step Functions state machine → CheckAvailability → PlaceOrder / NotifyCustomer → DynamoDB.

## Architecture

```
SQS: PlaceOrderQueue
        │ (BatchSize: 1)
        ▼
Lambda: TriggerSM          (starts Step Functions execution)
        │
        ▼
Step Functions: place-order (STANDARD)
        │
        ├─ CheckAvailability (Lambda)
        │         │
        ▼         ▼
   available?  not available?
        │                │
        ▼                ▼
  PlaceOrder        NotifyCustomer
  (→ DynamoDB)      (no-op notify)
        │
        ▼
  NotifyCustomer
```

## Lambda Functions

| Directory | Handler | Purpose |
|-----------|---------|---------|
| `functions/TriggerSM/` | `trigger.py` | SQS consumer — calls `states:StartExecution` |
| `functions/CheckAvailability/` | `checkAvailability.py` | Returns `{ available: true/false }` |
| `functions/PlaceOrder/` | `placeOrder.py` | Writes order to DynamoDB (`orders-<env>`) |
| `functions/NotifyCustomer/` | `notifyCustomer.py` | Notification stub |

> **Note:** The template declares `Runtime: nodejs12.x` but the handlers are `.py` files — the runtime should be updated to `python3.12` (or whichever Python version is in use).

## State Machine

Defined in `state.asl.json` (Amazon States Language).

> **Note:** `template.yml` references `DefinitionUri: statemachine/state.asl.json` but the file lives at the project root as `state.asl.json`. If deploying with SAM, either move the file to `statemachine/` or update the `DefinitionUri`.

Flow: `CheckAvailability` → `ValidateAvailability` (Choice) → `PlaceOrder` or `NotifyCustomer` → end.

## Infrastructure

**AWS SAM** (`template.yml`, transform `AWS::Serverless-2016-10-31`).

Key resources:
- `AWS::Serverless::StateMachine` — STANDARD type, CloudWatch logging (ALL level with execution data)
- `AWS::SQS::Queue` — `PlaceOrderQueue-<env>`
- `AWS::DynamoDB::Table` — `orders-<env>`, composite key `customer_id` (HASH) + `order_id` (RANGE), on-demand billing
- `AWS::Logs::LogGroup` — receives Step Functions execution logs

## Deploy

Requires the AWS SAM CLI.

```bash
sam build
sam deploy --guided   # first time — sets stack name, region, Environment parameter
sam deploy            # subsequent deploys (uses samconfig.toml)
```

The `Environment` parameter is appended to all resource names (e.g. `orders-dev`, `PlaceOrderQueue-prod`).

## Known Issues

- Runtime mismatch: `template.yml` specifies `nodejs12.x` but handlers are Python. Update to `python3.12`.
- `state.asl.json` path mismatch with `DefinitionUri` in the template — move to `statemachine/state.asl.json` or fix the path.
- `nodejs12.x` is end-of-life and no longer supported by Lambda.
