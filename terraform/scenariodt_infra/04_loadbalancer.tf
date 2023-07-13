# scenariodt Load Balancer
resource "aws_lb" "scenariodt-load-balancer" {
  name               = "${var.ecs_cluster_name}-alb"
  load_balancer_type = "application"
  internal           = false
  security_groups    = ["${data.terraform_remote_state.db.outputs.external_alb_sg_id}"]
  subnets            = ["${data.terraform_remote_state.db.outputs.public_subnet_1_id}", "${data.terraform_remote_state.db.outputs.public_subnet_2_id}"]
}

# Target group
resource "aws_alb_target_group" "default-target-group" {
  name     = "${var.ecs_cluster_name}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = "${data.terraform_remote_state.db.outputs.vpc_id}"

  health_check {
    path                = var.health_check_path
    port                = "traffic-port"
    healthy_threshold   = 5
    unhealthy_threshold = 5
    timeout             = 119
    interval            = 120
    matcher             = "200"
  }
}

# Listener (redirects traffic from the load balancer to the target group)
resource "aws_alb_listener" "scenariodt-ecs-alb-http-listener" {
  load_balancer_arn = aws_lb.scenariodt-load-balancer.id
  port              = "80"
  protocol          = "HTTP"
  depends_on        = [aws_alb_target_group.default-target-group]

  default_action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.default-target-group.arn
  }
}

# backend Load Balancer

resource "aws_lb" "backend-load-balancer" {
  name               = "${var.backend_cluster_name}-alb"
  load_balancer_type = "application"
  internal           = true
  security_groups    = [aws_security_group.backend-load-balancer-sg.id]
  subnets            = ["${data.terraform_remote_state.db.outputs.public_subnet_1_id}", "${data.terraform_remote_state.db.outputs.public_subnet_2_id}"]
}

# SDM Target group
resource "aws_alb_target_group" "sdm-target-group" {
  name     = "${var.backend_cluster_name}-sdm-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = "${data.terraform_remote_state.db.outputs.vpc_id}"

  health_check {
    path                = "/sdmhealth"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 119
    interval            = 120
    matcher             = "200-299"
  }
}

resource "aws_alb_target_group" "vis-target-group" {
  name     = "${var.backend_cluster_name}-vis-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = "${data.terraform_remote_state.db.outputs.vpc_id}"

  health_check {
    path                = "/vishealth"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 119
    interval            = 120
    matcher             = "200-299"
  }
}

# Listener (redirects traffic from the load balancer to the target group)
resource "aws_alb_listener" "backend-alb-http-listener" {
  load_balancer_arn = aws_lb.backend-load-balancer.id
  port              = "80"
  protocol          = "HTTP"
  depends_on        = [aws_alb_target_group.sdm-target-group, aws_alb_target_group.vis-target-group]

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Fixed response content"
      status_code  = "200"
    }
  }
}

resource "aws_alb_listener_rule" "sdm" {
  listener_arn = aws_alb_listener.backend-alb-http-listener.arn

  action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.sdm-target-group.arn
  }

  condition {
    path_pattern {
      values = ["/predictions"]
    }
  }
}

resource "aws_alb_listener_rule" "vis" {
  listener_arn = aws_alb_listener.backend-alb-http-listener.arn

  action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.vis-target-group.arn
  }

  condition {
    path_pattern {
      values = ["/plot"]
    }
  }
}

