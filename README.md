# Microservices Order System 

An event-driven order processing platform — 4 independent Flask microservices that communicate through AWS SNS/SQS instead of calling each other directly.

## Why build it this way
Most beginner projects are one app talking to one database. This one isn't. If Notification service goes down, orders still get created and stock still updates — that's the whole point of loose coupling. Order service publishes an event and moves on; it never waits for Inventory or Notification to respond.

##  Architecture

### Tech Stack
- **Backend:** Flask, boto3, SQLite, Python 3.10
- **Messaging:** AWS SNS (fan-out), AWS SQS (2 queues)
- **Container:** Docker, Docker Compose, Amazon ECR (4 repos)
- **IaC:** Terraform — VPC, messaging, IAM, zero hourly cost
- **CI/CD:** GitHub Actions, matrix strategy for parallel builds
- **Monitoring:** Prometheus + Grafana, one dashboard for all 4 services
Client → API Gateway → Order Service → publishes to SNS

↓ fans out to

Inventory Queue   Notification Queue

↓                  ↓

Inventory Service   Notification Service

(reduces stock)      (sends email)

##  Features

###  Implemented
- 4 independent microservices, each owning its own data
- SNS fan-out — one event delivered to two queues, processed independently
- 5 least-privilege IAM roles, one per service
- Zero-cost infra — no NAT Gateway, no ECS, no load balancer
- Parallel CI/CD — all 4 services tested and built at once
- Centralized monitoring across all 4 services

###  In Progress
- Real ECS Fargate deployment (currently Docker Compose only)
- SES production access (currently sandbox, logs instead of sending)

##  Quick Start

```bash
git clone https://github.com/rohan-rajesh94/aws-microservices-order-system
cd aws-microservices-order-system

echo "AWS_ACCESS_KEY_ID=your-key" >> .env
echo "AWS_SECRET_ACCESS_KEY=your-secret" >> .env

cd infra && terraform apply -auto-approve && cd ..
docker-compose up --build
```

### Test it
```bash
curl http://localhost:5000/api/stock
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"product_name": "shoes", "quantity": 5, "customer_email": "test@test.com"}'
# wait ~15s, check again
curl http://localhost:5000/api/stock
```