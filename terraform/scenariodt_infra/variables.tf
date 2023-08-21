variable "public_subnet_1_cidr" {
  description = "CIDR Block for Public Subnet 1"
  default     = "10.0.1.0/24"
}
variable "public_subnet_2_cidr" {
  description = "CIDR Block for Public Subnet 2"
  default     = "10.0.2.0/24"
}
variable "private_subnet_1_cidr" {
  description = "CIDR Block for Private Subnet 1"
  default     = "10.0.3.0/24"
}
variable "private_subnet_2_cidr" {
  description = "CIDR Block for Private Subnet 2"
  default     = "10.0.4.0/24"
}
variable "availability_zone_1" {
  description = "Availability zone 1"
  default     = "eu-central-1b"
}
variable "availability_zone_2" {
  description = "Availability zone 2"
  default     = "eu-central-1c"
}

# load balancer

variable "health_check_path" {
  description = "Health check path for the default target group"
  default     = "/ping/"
}

# ecs

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  default     = "scenariodt"
}
variable "backend_cluster_name" {
  description = "Name of the ECS cluster"
  default     = "backend"
}
variable "ami" {
  description = "Which AMI to spawn."
  default = "ami-08d7cc30c35e1adbd"
}
variable "instance_type" {
  default = "t2.micro"
}

variable "app_count" {
  description = "Number of scenariodt containers to run"
  default     = 1
}

variable "sdm_count" {
  description = "Number of scenariodt containers to run"
  default     = 2
}

variable "vis_count" {
  description = "Number of scenariodt containers to run"
  default     = 2
}

variable "docker_image_url_django" {
  description = "Docker image for Django"
  default     = "vasilis421/scenario_dt:latest"
}
variable "docker_image_url_sdm" {
  description = "Docker image for the SDM R API"
  default     = "vasilis421/r-sdm-api:latest"
}
variable "docker_image_url_vis" {
  description = "Docker image for the Visualization R API"
  default     = "vasilis421/r-vis-api:latest"
}
variable "docker_image_url_nginx" {
  description = "Docker image for NGINX"
  default     = "vasilis421/nginx:latest"
}

# key pair

variable "ssh_pubkey_file" {
  description = "Path to an SSH public key"
  default     = "~/.ssh/id_rsa.pub"
}

variable "backend_ssh_pubkey_file" {
  description = "Path to an SSH public key"
  default     = "~/.ssh/id_rsa.pub"
}

# logs

variable "log_retention_in_days" {
  default = 1
}

# aws config

variable "aws_access_key" {
  default = " "
}

variable "aws_secret_key" {
  default = " "
}

variable "region" {
  description = "The AWS region to create resources in"
  default     = "eu-central-1"
}

# auto scaling

variable "autoscale_min" {
  description = "Minimum autoscale (number of EC2)"
  default     = "1"
}
variable "autoscale_max" {
  description = "Maximum autoscale (number of EC2)"
  default     = "5"
}
variable "autoscale_desired" {
  description = "Desired autoscale (number of EC2)"
  default     = "1"
}


variable "backend_autoscale_min" {
  description = "Minimum autoscale (number of EC2)"
  default     = "4"
}
variable "backend_autoscale_max" {
  description = "Maximum autoscale (number of EC2)"
  default     = "10"
}
variable "backend_autoscale_desired" {
  description = "Desired autoscale (number of EC2)"
  default     = "4"
}

# RDS

variable "rds_db_name" {
  description = "RDS database name"
  default     = "user_db"
}
variable "rds_username" {
  description = "RDS database username"
  default     = "dtcloudthesis"
}
variable "rds_password" {
  description = "RDS database password"
  default     = "dtcloudthesis"
}
variable "rds_instance_class" {
  description = "RDS instance type"
  default     = "db.t3.micro"
}
variable "rds_port" {
  description = "RDS port"
  default     = "5432"
}