# Production VPC
resource "aws_vpc" "scenariodt-vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
}

# Public subnets
resource "aws_subnet" "scenariodt-public-subnet-1" {
  cidr_block        = var.public_subnet_1_cidr
  vpc_id            = aws_vpc.scenariodt-vpc.id
  availability_zone = var.availability_zone_1
}
resource "aws_subnet" "scenariodt-public-subnet-2" {
  cidr_block        = var.public_subnet_2_cidr
  vpc_id            = aws_vpc.scenariodt-vpc.id
  availability_zone = var.availability_zone_2
}

# Private subnets
resource "aws_subnet" "scenariodt-private-subnet-1" {
  cidr_block        = var.private_subnet_1_cidr
  vpc_id            = aws_vpc.scenariodt-vpc.id
  availability_zone = var.availability_zone_1
}
resource "aws_subnet" "scenariodt-private-subnet-2" {
  cidr_block        = var.private_subnet_2_cidr
  vpc_id            = aws_vpc.scenariodt-vpc.id
  availability_zone = var.availability_zone_2
}

# Route tables for the subnets
resource "aws_route_table" "scenariodt-public-route-table" {
  vpc_id = aws_vpc.scenariodt-vpc.id
}
resource "aws_route_table" "scenariodt-private-route-table" {
  vpc_id = aws_vpc.scenariodt-vpc.id
}

# Associate the newly created route tables to the subnets
resource "aws_route_table_association" "scenariodt-public-route-1-association" {
  route_table_id = aws_route_table.scenariodt-public-route-table.id
  subnet_id      = aws_subnet.scenariodt-public-subnet-1.id
}
resource "aws_route_table_association" "scenariodt-public-route-2-association" {
  route_table_id = aws_route_table.scenariodt-public-route-table.id
  subnet_id      = aws_subnet.scenariodt-public-subnet-2.id
}
resource "aws_route_table_association" "scenariodt-private-route-1-association" {
  route_table_id = aws_route_table.scenariodt-private-route-table.id
  subnet_id      = aws_subnet.scenariodt-private-subnet-1.id
}
resource "aws_route_table_association" "scenariodt-private-route-2-association" {
  route_table_id = aws_route_table.scenariodt-private-route-table.id
  subnet_id      = aws_subnet.scenariodt-private-subnet-2.id
}

# Internet Gateway for the public subnet
resource "aws_internet_gateway" "scenariodt-igw" {
  vpc_id = aws_vpc.scenariodt-vpc.id
}

# Route the public subnet traffic through the Internet Gateway
resource "aws_route" "scenariodt-public-internet-igw-route" {
  route_table_id         = aws_route_table.scenariodt-public-route-table.id
  gateway_id             = aws_internet_gateway.scenariodt-igw.id
  destination_cidr_block = "0.0.0.0/0"
}

# S3 gateway endpoint
resource "aws_vpc_endpoint" "s3" {
  vpc_id              = aws_vpc.scenariodt-vpc.id
  service_name        = "com.amazonaws.eu-central-1.s3"
  route_table_ids = [aws_route_table.scenariodt-public-route-table.id]
}
