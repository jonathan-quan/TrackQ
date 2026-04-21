output "alb_dns_name" {
  description = "Public DNS name of the load balancer."
  value       = aws_lb.backend.dns_name
}

output "backend_base_url" {
  description = "Base URL for the deployed backend."
  value       = "http://${aws_lb.backend.dns_name}"
}

output "health_check_url" {
  description = "Public health check URL."
  value       = "http://${aws_lb.backend.dns_name}${var.health_check_path}"
}

output "ecr_repository_url" {
  description = "Push backend images to this ECR repository."
  value       = aws_ecr_repository.backend.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.backend.name
}

output "ecs_service_name" {
  description = "ECS service name."
  value       = aws_ecs_service.backend.name
}

output "db_endpoint" {
  description = "RDS endpoint address."
  value       = aws_db_instance.backend.address
}

output "app_secret_arn" {
  description = "Secrets Manager secret ARN containing backend environment values."
  value       = aws_secretsmanager_secret.app.arn
}
