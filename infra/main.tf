terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "task_execution_secrets" {
  statement {
    actions = ["secretsmanager:GetSecretValue"]

    resources = [aws_secretsmanager_secret.app.arn]
  }
}

locals {
  name          = lower(replace(var.app_name, "/[^a-zA-Z0-9-]/", "-"))
  resource_name = substr(local.name, 0, 20)
  azs           = slice(data.aws_availability_zones.available.names, 0, 2)

  tags = merge(
    {
      Application = var.app_name
      ManagedBy   = "terraform"
    },
    var.tags
  )
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, {
    Name = "${local.resource_name}-vpc"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.tags, {
    Name = "${local.resource_name}-igw"
  })
}

resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = local.azs[count.index % length(local.azs)]
  map_public_ip_on_launch = true

  tags = merge(local.tags, {
    Name = "${local.resource_name}-public-${count.index + 1}"
    Tier = "public"
  })
}

resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = local.azs[count.index % length(local.azs)]

  tags = merge(local.tags, {
    Name = "${local.resource_name}-private-${count.index + 1}"
    Tier = "private"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.tags, {
    Name = "${local.resource_name}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.tags, {
    Name = "${local.resource_name}-private-rt"
  })
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "alb" {
  name        = "${local.resource_name}-alb-sg"
  description = "Allow HTTP traffic to the public load balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.resource_name}-alb-sg"
  })
}

resource "aws_security_group" "ecs" {
  name        = "${local.resource_name}-ecs-sg"
  description = "Allow ALB traffic into ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "App traffic from ALB"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.resource_name}-ecs-sg"
  })
}

resource "aws_security_group" "db" {
  name        = "${local.resource_name}-db-sg"
  description = "Allow MySQL traffic from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MySQL from ECS"
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.resource_name}-db-sg"
  })
}

resource "aws_ecr_repository" "backend" {
  name                 = "anhquan/trackq"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the most recent 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "aws_db_subnet_group" "backend" {
  name       = "${local.resource_name}-db-subnets"
  subnet_ids = aws_subnet.private[*].id

  tags = merge(local.tags, {
    Name = "${local.resource_name}-db-subnets"
  })
}

resource "aws_db_instance" "backend" {
  identifier                 = "${local.name}-db"
  engine                     = "mysql"
  engine_version             = var.db_engine_version
  instance_class             = var.db_instance_class
  allocated_storage          = var.db_allocated_storage
  max_allocated_storage      = var.db_max_allocated_storage
  storage_type               = "gp3"
  storage_encrypted          = true
  db_name                    = var.db_name
  username                   = var.db_username
  password                   = random_password.db_password.result
  port                       = var.db_port
  db_subnet_group_name       = aws_db_subnet_group.backend.name
  vpc_security_group_ids     = [aws_security_group.db.id]
  backup_retention_period    = var.backup_retention_days
  skip_final_snapshot        = var.skip_final_snapshot
  deletion_protection        = false
  publicly_accessible        = false
  auto_minor_version_upgrade = true
  apply_immediately          = true

  tags = local.tags
}

resource "aws_secretsmanager_secret" "app" {
  name = "${local.name}/app-env"

  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id

  secret_string = jsonencode({
    SECRET_KEY                  = random_password.jwt_secret.result
    ACCESS_TOKEN_EXPIRE_MINUTES = tostring(var.access_token_expire_minutes)
    DATABASE_URL = format(
      "mysql+pymysql://%s:%s@%s:%d/%s",
      var.db_username,
      random_password.db_password.result,
      aws_db_instance.backend.address,
      aws_db_instance.backend.port,
      var.db_name
    )
    CORS_ALLOW_ORIGINS = join(",", var.cors_allow_origins)
  })
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name}"
  retention_in_days = 30

  tags = local.tags
}

resource "aws_ecs_cluster" "backend" {
  name = "${local.name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.tags
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${local.name}-task-exec"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_managed" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name   = "${local.name}-task-exec-secrets"
  role   = aws_iam_role.ecs_task_execution.id
  policy = data.aws_iam_policy_document.task_execution_secrets.json
}

resource "aws_iam_role" "ecs_task" {
  name               = "${local.name}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json

  tags = local.tags
}

resource "aws_lb" "backend" {
  name               = "${local.resource_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = local.tags
}

resource "aws_lb_target_group" "backend" {
  name        = "${local.resource_name}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = var.health_check_path
    matcher             = "200-399"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    interval            = 30
    timeout             = 5
  }

  tags = local.tags
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = local.name
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = local.name
      image     = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "PYTHONUNBUFFERED"
          value = "1"
        }
      ]
      secrets = [
        {
          name      = "SECRET_KEY"
          valueFrom = "${aws_secretsmanager_secret.app.arn}:SECRET_KEY::"
        },
        {
          name      = "ACCESS_TOKEN_EXPIRE_MINUTES"
          valueFrom = "${aws_secretsmanager_secret.app.arn}:ACCESS_TOKEN_EXPIRE_MINUTES::"
        },
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.app.arn}:DATABASE_URL::"
        },
        {
          name      = "CORS_ALLOW_ORIGINS"
          valueFrom = "${aws_secretsmanager_secret.app.arn}:CORS_ALLOW_ORIGINS::"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }
    }
  ])

  tags = local.tags
}

resource "aws_ecs_service" "backend" {
  name                               = "${local.name}-service"
  cluster                            = aws_ecs_cluster.backend.id
  task_definition                    = aws_ecs_task_definition.backend.arn
  desired_count                      = var.desired_count
  launch_type                        = "FARGATE"
  platform_version                   = "LATEST"
  health_check_grace_period_seconds  = 60
  wait_for_steady_state              = false
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = local.name
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.http]

  tags = local.tags
}
