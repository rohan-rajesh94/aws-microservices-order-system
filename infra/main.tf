terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source               = "./modules/vpc"
  project_name         = var.project_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

module "messaging" {
  source       = "./modules/messaging"
  project_name = var.project_name
}
module "iam" {
  source                  = "./modules/iam"
  project_name            = var.project_name
  aws_region              = var.aws_region
  sns_topic_arn           = module.messaging.sns_topic_arn
  inventory_queue_arn     = module.messaging.inventory_queue_arn
  notification_queue_arn  = module.messaging.notification_queue_arn
}