resource "aws_db_subnet_group" "user-db-subnet-group" {
  name       = "main"
  subnet_ids = [aws_subnet.scenariodt-private-subnet-1.id, aws_subnet.scenariodt-private-subnet-2.id]
}

resource "aws_db_instance" "user-db" {
  identifier              = "user-db"
  db_name                 = var.rds_db_name
  username                = var.rds_username
  password                = var.rds_password
  port                    = "5432"
  engine                  = "postgres"
  engine_version          = "14.7"
  instance_class          = var.rds_instance_class
  allocated_storage       = "10"
  storage_encrypted       = false
  vpc_security_group_ids  = [aws_security_group.rds.id]
  db_subnet_group_name    = aws_db_subnet_group.user-db-subnet-group.name
  multi_az                = false
  storage_type            = "gp2"
  publicly_accessible     = false
  backup_retention_period = 0
  skip_final_snapshot     = true
}