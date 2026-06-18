# Gateway SG — only one exposed to internet via ALB later
resource "aws_security_group" "gateway" {
  name   = "${var.project_name}-gateway-sg"
  vpc_id = var.vpc_id

  ingress {
    description = "From ALB"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # simplified — ALB SG would be tighter in full prod
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-gateway-sg" }
}

# Internal services SG — only Gateway can call these directly
resource "aws_security_group" "internal" {
  name   = "${var.project_name}-internal-sg"
  vpc_id = var.vpc_id

  ingress {
    description     = "Order service from Gateway"
    from_port       = 5001
    to_port         = 5001
    protocol        = "tcp"
    security_groups = [aws_security_group.gateway.id]
  }

  ingress {
    description     = "Inventory service from Gateway"
    from_port       = 5002
    to_port         = 5002
    protocol        = "tcp"
    security_groups = [aws_security_group.gateway.id]
  }

  ingress {
    description     = "Notification service from Gateway"
    from_port       = 5003
    to_port         = 5003
    protocol        = "tcp"
    security_groups = [aws_security_group.gateway.id]
  }

  # Allow services to talk to each other for Prometheus scraping
  ingress {
    description = "Internal Prometheus scraping"
    from_port   = 5000
    to_port     = 5003
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-internal-sg" }
}

# Monitoring SG — Prometheus and Grafana
resource "aws_security_group" "monitoring" {
  name   = "${var.project_name}-monitoring-sg"
  vpc_id = var.vpc_id

  ingress {
    description     = "Prometheus"
    from_port       = 9090
    to_port         = 9090
    protocol        = "tcp"
    security_groups = [aws_security_group.gateway.id]
  }

  ingress {
    description     = "Grafana"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.gateway.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-monitoring-sg" }
}