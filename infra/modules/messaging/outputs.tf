output "sns_topic_arn"          { value = aws_sns_topic.order_events.arn }
output "inventory_queue_url"    { value = aws_sqs_queue.inventory_queue.url }
output "notification_queue_url" { value = aws_sqs_queue.notification_queue.url }