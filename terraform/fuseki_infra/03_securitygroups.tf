# Fuseki ECS Security group (traffic -> ECS)
resource "aws_security_group" "fuseki-ecs-sg" {
  name        = "fuseki_ecs_security_group"
  description = "Allows inbound access"
  vpc_id      = aws_vpc.fuseki-vpc.id

  ingress {
    from_port       = 3030
    to_port         = 3030
    protocol        = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}