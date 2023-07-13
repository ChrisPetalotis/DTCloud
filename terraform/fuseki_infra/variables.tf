variable "vpc_cidr" {
  description = "CIDR Block for Fuseki VPC"
  default     = "192.168.0.0/16"
}

variable "public_subnet_1_cidr" {
  description = "CIDR Block for Public Subnet 1"
  default     = "192.168.10.0/24"
}
variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["eu-central-1b", "eu-central-1c"]
}

# ecs

variable "fuseki_ecs_cluster_name" {
  description = "Name of the Fuseki ECS cluster"
  default     = "fuseki"
}
variable "ami" {
  description = "Which AMI to spawn."
  default = "ami-08d7cc30c35e1adbd"
}
variable "instance_type" {
  default = "t2.micro"
}
variable "fuseki_count" {
  description = "Number of Fuseki containers to run"
  default     = 1
}
variable "docker_image_url_fuseki" {
  description = "Docker image for Apache Jena Fuseki"
  default     = "secoresearch/fuseki:latest"
}

# fuseki env

variable "fuseki_pwd" {
  description = "Fuseki Admin Password"
  default     = "pw123"
}
variable "fuseki_timeout" {
  description = "Fuseki Timeout"
  default     = "60000"
}

# key pair

variable "fuseki_ssh_pubkey_file" {
  description = "Path to an SSH public key"
  default     = "~/.ssh/id_rsa.pub"
}

# logs

variable "log_retention_in_days" {
  default = 1
}

# aws config

variable "aws_access_key" {
  default = "AKIASF7WZIHBGWAVP57T"
}

variable "aws_secret_key" {
  default = "Ei3Dq8/uYPiyO0V5d1KMyL6Wi/wGW5D3JyVSc24e"
}

variable "region" {
  description = "The AWS region to create resources in."
  default     = "eu-central-1"
}