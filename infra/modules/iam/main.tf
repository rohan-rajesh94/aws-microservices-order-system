# ── ECS Execution Role — shared by all 4 services ──────────
# Used by ECS itself to pull images and write logs
resource "aws_iam_role" "ecs_execution" {
  name = "${var.project_name}-ecs-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ── Order Service Task Role — can ONLY publish to SNS ───────
resource "aws_iam_role" "order_task" {
  name = "${var.project_name}-order-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "order_sns_publish" {
  name = "sns-publish-only"
  role = aws_iam_role.order_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sns:Publish"]
      Resource = var.sns_topic_arn
    }]
  })
}

# ── Inventory Service Task Role — can ONLY read its own queue ─
resource "aws_iam_role" "inventory_task" {
  name = "${var.project_name}-inventory-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "inventory_sqs_consume" {
  name = "sqs-consume-only"
  role = aws_iam_role.inventory_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ]
      Resource = var.inventory_queue_arn
    }]
  })
}

# ── Notification Service Task Role — can ONLY read its queue + send SES ─
resource "aws_iam_role" "notification_task" {
  name = "${var.project_name}-notification-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "notification_permissions" {
  name = "sqs-and-ses"
  role = aws_iam_role.notification_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.notification_queue_arn
      },
      {
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
      }
    ]
  })
}

# ── API Gateway Task Role — no AWS permissions needed ───────
# It only makes HTTP calls to other services, not AWS APIs
resource "aws_iam_role" "gateway_task" {
  name = "${var.project_name}-gateway-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}