# SNS Topic — the "loudspeaker" Order service publishes to
resource "aws_sns_topic" "order_events" {
  name = "${var.project_name}-order-events"
  tags = { Name = "${var.project_name}-order-events" }
}

# SQS Queue 1 — Inventory service's own mailbox
resource "aws_sqs_queue" "inventory_queue" {
  name                       = "${var.project_name}-inventory-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 86400  # keep unprocessed messages 1 day
  tags = { Name = "${var.project_name}-inventory-queue" }
}

# SQS Queue 2 — Notification service's own mailbox
resource "aws_sqs_queue" "notification_queue" {
  name                       = "${var.project_name}-notification-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 86400
  tags = { Name = "${var.project_name}-notification-queue" }
}

# Policy — allows SNS to send messages INTO inventory queue
resource "aws_sqs_queue_policy" "inventory_policy" {
  queue_url = aws_sqs_queue.inventory_queue.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.inventory_queue.arn
      Condition = {
        ArnEquals = { "aws:SourceArn" = aws_sns_topic.order_events.arn }
      }
    }]
  })
}

# Policy — allows SNS to send messages INTO notification queue
resource "aws_sqs_queue_policy" "notification_policy" {
  queue_url = aws_sqs_queue.notification_queue.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.notification_queue.arn
      Condition = {
        ArnEquals = { "aws:SourceArn" = aws_sns_topic.order_events.arn }
      }
    }]
  })
}

# Subscribe inventory queue to the SNS topic — THIS creates the fan-out
resource "aws_sns_topic_subscription" "inventory_sub" {
  topic_arn = aws_sns_topic.order_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.inventory_queue.arn
}

# Subscribe notification queue to the SAME SNS topic — second fan-out copy
resource "aws_sns_topic_subscription" "notification_sub" {
  topic_arn = aws_sns_topic.order_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.notification_queue.arn
}