output "vpc_id" {
  value = aws_vpc.scenariodt-vpc.id
}

output "public_subnet_1_id" {
  value = aws_subnet.scenariodt-public-subnet-1.id
}

output "public_subnet_2_id" {
  value = aws_subnet.scenariodt-public-subnet-2.id
}

output "private_subnet_1_id" {
  value = aws_subnet.scenariodt-private-subnet-1.id
}

output "private_subnet_2_id" {
  value = aws_subnet.scenariodt-private-subnet-2.id
}

output "external_alb_sg_id" {
  value = aws_security_group.scenariodt-load-balancer-sg.id
}

output "scenariodt_ecs_sg_id" {
  value = aws_security_group.scenariodt-ecs-sg.id
}

output "user_db_address" {
  value = aws_db_instance.user-db.address
}

