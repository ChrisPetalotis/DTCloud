# Production VPC
resource "aws_vpc" "fuseki-vpc" {
  cidr_block           = "192.168.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
}

# Public subnets
resource "aws_subnet" "fuseki-public-subnet-1" {
  cidr_block        = var.public_subnet_1_cidr
  vpc_id            = aws_vpc.fuseki-vpc.id
  availability_zone = var.availability_zones[0]
}

# Route tables for the subnets
resource "aws_route_table" "fuseki-public-route-table" {
  vpc_id = aws_vpc.fuseki-vpc.id
}

# Associate the newly created route tables to the subnets
resource "aws_route_table_association" "fuseki-public-route-1-association" {
  route_table_id = aws_route_table.fuseki-public-route-table.id
  subnet_id      = aws_subnet.fuseki-public-subnet-1.id
}

# Internet Gateway for the public subnet
resource "aws_internet_gateway" "fuseki-igw" {
  vpc_id = aws_vpc.fuseki-vpc.id
}

# Route the public subnet traffic through the Internet Gateway
resource "aws_route" "fuseki-public-internet-igw-route" {
  route_table_id         = aws_route_table.fuseki-public-route-table.id
  gateway_id             = aws_internet_gateway.fuseki-igw.id
  destination_cidr_block = "0.0.0.0/0"
}