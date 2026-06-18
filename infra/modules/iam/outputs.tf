output "ecs_execution_role_arn"   { value = aws_iam_role.ecs_execution.arn }
output "order_task_role_arn"      { value = aws_iam_role.order_task.arn }
output "inventory_task_role_arn"  { value = aws_iam_role.inventory_task.arn }
output "notification_task_role_arn" { value = aws_iam_role.notification_task.arn }
output "gateway_task_role_arn"    { value = aws_iam_role.gateway_task.arn }