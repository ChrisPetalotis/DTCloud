data "terraform_remote_state" "db" {
  backend = "local"

  config = {
    path = "${path.module}/../db/terraform.tfstate"
  }
}

# Backend ALB Security Group (Traffic Internet -> ALB)
resource "aws_security_group" "backend-load-balancer-sg" {
  name        = "backend_load_balancer_security_group"
  description = "Controls access to the backend ALB"
  vpc_id      = "${data.terraform_remote_state.db.outputs.vpc_id}"

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = ["${data.terraform_remote_state.db.outputs.scenariodt_ecs_sg_id}"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "backend-sg" {
  name        = "backend_security_group"
  description = "Controls access to the backend services"
  vpc_id      = "${data.terraform_remote_state.db.outputs.vpc_id}"

   ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.backend-load-balancer-sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}