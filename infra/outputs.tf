output "vpc_id"               { value = module.vpc.vpc_id }
output "public_subnet_ids"    { value = module.vpc.public_subnet_ids }
output "private_subnet_ids"   { value = module.vpc.private_subnet_ids }
output "sns_topic_arn"        { value = module.messaging.sns_topic_arn }
output "inventory_queue_url"  { value = module.messaging.inventory_queue_url }
output "notification_queue_url" { value = module.messaging.notification_queue_url }