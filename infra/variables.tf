variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Base name used across AWS resources."
  type        = string
  default     = "trackq-backend"
}

variable "image_tag" {
  description = "Docker image tag to run from the ECR repository."
  type        = string
  default     = "latest"
}

variable "container_port" {
  description = "Port exposed by the FastAPI container."
  type        = number
  default     = 8000
}

variable "health_check_path" {
  description = "ALB health check path."
  type        = string
  default     = "/health"
}

variable "desired_count" {
  description = "Number of ECS tasks to keep running."
  type        = number
  default     = 1
}

variable "task_cpu" {
  description = "CPU units for the Fargate task definition."
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Memory in MiB for the Fargate task definition."
  type        = number
  default     = 1024
}

variable "vpc_cidr" {
  description = "CIDR block for the deployment VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets used by the ALB and ECS tasks."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]

  validation {
    condition     = length(var.public_subnet_cidrs) >= 2
    error_message = "Provide at least two public subnet CIDR blocks."
  }
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets used by RDS."
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]

  validation {
    condition     = length(var.private_subnet_cidrs) >= 2
    error_message = "Provide at least two private subnet CIDR blocks."
  }
}

variable "db_name" {
  description = "Initial MySQL database name."
  type        = string
  default     = "trackq_db"
}

variable "db_username" {
  description = "RDS master username and app username."
  type        = string
  default     = "trackq_user"
}

variable "db_port" {
  description = "MySQL port."
  type        = number
  default     = 3306
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.micro"
}

variable "db_engine_version" {
  description = "Optional MySQL engine version. Set to null to use the AWS default."
  type        = string
  default     = null
}

variable "db_allocated_storage" {
  description = "Initial RDS storage in GiB."
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum autoscaled RDS storage in GiB."
  type        = number
  default     = 100
}

variable "backup_retention_days" {
  description = "How many days to retain RDS automated backups."
  type        = number
  default     = 7
}

variable "skip_final_snapshot" {
  description = "Skip the final snapshot when destroying the RDS instance."
  type        = bool
  default     = true
}

variable "access_token_expire_minutes" {
  description = "JWT access token lifetime passed into the container."
  type        = number
  default     = 30
}

variable "cors_allow_origins" {
  description = "Origins allowed by the FastAPI CORS middleware."
  type        = list(string)
  default     = ["http://localhost:5173", "http://localhost:3000"]
}

variable "tags" {
  description = "Additional tags applied to AWS resources."
  type        = map(string)
  default     = {}
}
