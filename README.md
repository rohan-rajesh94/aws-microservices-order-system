# aws-microservices-order-system

> Event-driven order processing system — 4 microservices talking through AWS SNS/SQS instead of calling each other directly.

## What this does
When someone places an order, the Order service saves it and announces it on an SNS topic. Two other services — Inventory and Notification — independently hear that announcement through their own SQS queues and react: one reduces stock, the other sends an email. None of them call each other directly.

## Why build it this way
Most beginner projects are one app talking to one database. This one isn't. It's 4 small Flask services that don't know about each other — they only know about a message queue. If Notification service goes down, orders still get created and stock still updates. That's the whole point of loose coupling.

## Architecture
Client → API Gateway → Order Service → publishes to SNS

↓ fans out to

Inventory Queue   Notification Queue

↓                  ↓

Inventory Service   Notification Service

(reduces stock)      (sends email)

## Stack
Python, Flask, boto3, AWS SNS, AWS SQS, Terraform, Docker, GitHub Actions, Prometheus, Grafana

## Services
| Service | Port | Job |
|---|---|---|
| api-gateway | 5000 | front door, routes everything |
| order-service | 5001 | creates orders, publishes events |
| inventory-service | 5002 | listens for events, updates stock |
| notification-service | 5003 | listens for events, sends emails |

## Running it locally
```bash
# add your AWS keys to .env first
docker-compose up --build
```

## Testing the flow
```bash
curl http://localhost:5000/api/stock
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"product_name": "shoes", "quantity": 5, "customer_email": "test@test.com"}'

# wait ~15s for the queues to process
curl http://localhost:5000/api/stock
curl http://localhost:5000/api/notifications
```

## Infrastructure
```bash
cd infra
terraform apply -auto-approve   # creates VPC, SNS, SQS, IAM — all free tier
terraform destroy -auto-approve # clean up after testing
```

No NAT Gateway, no ECS, no load balancer — kept this one at zero ongoing cost on purpose. Services run locally but talk to real AWS messaging infrastructure.

## CI/CD
GitHub Actions tests and builds all 4 services in parallel using a matrix strategy, pushes each to its own ECR repo, then validates the Terraform.

## Monitoring
One Prometheus instance scrapes all 4 services, one Grafana dashboard shows them together.

