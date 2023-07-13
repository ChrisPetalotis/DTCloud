resource "aws_ecs_cluster" "scenariodt-cluster" {
  name = "${var.ecs_cluster_name}-cluster"
}

resource "aws_launch_configuration" "ecs" {
  name_prefix                 = "${var.ecs_cluster_name}-cluster-"
  image_id                    = var.ami
  instance_type               = var.instance_type
  security_groups             = ["${data.terraform_remote_state.db.outputs.scenariodt_ecs_sg_id}"]
  iam_instance_profile        = aws_iam_instance_profile.scenariodt.name
  key_name                    = aws_key_pair.scenariodt-kp.key_name
  associate_public_ip_address = true
  enable_monitoring           = false
  user_data                   = "#!/bin/bash\necho ECS_CLUSTER='${var.ecs_cluster_name}-cluster' >> /etc/ecs/ecs.config"
}

data "terraform_remote_state" "fuseki" {
  backend = "local"

  config = {
    path = "${path.module}/../fuseki_infra/terraform.tfstate"
  }
}

data "template_file" "app" {
  template = file("templates/django_app.json.tpl")

  vars = {
    django_container_name   = "scenario_dt"
    docker_image_url_django = "vasilis421/scenario_dt:latest"
    django_container_cpu    = 512
    django_container_memory = 500
    django_container_port   = 8000
    django_host_port        = 8000
    django_command          = "python manage.py makemigrations && python manage.py collectstatic --no-input && python manage.py migrate && gunicorn scenariodt.wsgi:application --timeout 120 --bind 0.0.0.0:8000"
    region                  = var.region
    rds_db_name             = var.rds_db_name
    rds_username            = var.rds_username
    rds_password            = var.rds_password
    rds_hostname            = "${data.terraform_remote_state.db.outputs.user_db_address}"
    rds_port                = var.rds_port
    aws_access_key          = var.aws_access_key
    aws_secret_key          = var.aws_secret_key
    sparql_endpoint         = "${data.terraform_remote_state.fuseki.outputs.fuseki_instance_ip}"
    sdm_endpoint            = "${aws_lb.backend-load-balancer.dns_name}"
    vis_endpoint            = "${aws_lb.backend-load-balancer.dns_name}"
    
    nginx_container_name    = "nginx"
    docker_image_url_nginx  = "vasilis421/nginx:latest"
    nginx_container_cpu     = 512
    nginx_container_memory  = 400
    nginx_container_port    = 80
    nginx_host_port         = 80
  }
}

resource "aws_ecs_task_definition" "app" {
  family                = "scenario_dt"
  container_definitions = data.template_file.app.rendered
  network_mode          = "bridge"
}

resource "aws_ecs_service" "scenariodt" {
  name                   = "${var.ecs_cluster_name}-service"
  cluster                = aws_ecs_cluster.scenariodt-cluster.id
  task_definition        = aws_ecs_task_definition.app.arn
  iam_role               = aws_iam_role.scenariodt-service-role.arn
  desired_count          = var.app_count
  depends_on             = [aws_alb_listener.scenariodt-ecs-alb-http-listener, aws_iam_role_policy.scenariodt-service-role-policy]
  
  load_balancer {
    target_group_arn = aws_alb_target_group.default-target-group.arn
    container_name   = "nginx"
    container_port   = 80
  }
}


resource "aws_ecs_cluster" "backend-cluster" {
  name = "${var.backend_cluster_name}-cluster"
}

resource "aws_launch_configuration" "backend" {
  name_prefix                 = "${var.backend_cluster_name}-cluster-"
  image_id                    = var.ami
  instance_type               = var.instance_type
  security_groups             = [aws_security_group.backend-sg.id]
  iam_instance_profile        = aws_iam_instance_profile.scenariodt.name
  key_name                    = aws_key_pair.backend-kp.key_name
  associate_public_ip_address = true
  enable_monitoring           = false
  user_data                   = "#!/bin/bash\necho ECS_CLUSTER='${var.backend_cluster_name}-cluster' >> /etc/ecs/ecs.config"
}

data "template_file" "sdm" {
  template = file("templates/sdm.json.tpl")

  vars = {
    sdm_container_name   = "sdm"
    docker_image_url_sdm = "vasilis421/r-sdm-api:latest"
    sdm_container_cpu    = 850
    sdm_container_memory = 600
    sdm_container_port   = 80
    sdm_host_port        = 8005
    region               = var.region
  }
}

resource "aws_ecs_task_definition" "sdm" {
  family                = "sdm"
  container_definitions = data.template_file.sdm.rendered
  network_mode          = "bridge"
}

resource "aws_ecs_service" "sdm" {
  name                   = "sdm-service"
  cluster                = aws_ecs_cluster.backend-cluster.id
  task_definition        = aws_ecs_task_definition.sdm.arn
  iam_role               = aws_iam_role.scenariodt-service-role.arn
  desired_count          = var.sdm_count
  depends_on             = [aws_alb_listener_rule.sdm, aws_iam_role_policy.scenariodt-service-role-policy]
  
  load_balancer {
    target_group_arn = aws_alb_target_group.sdm-target-group.arn
    container_name   = "sdm"
    container_port   = 80
  }
}


data "template_file" "vis" {
  template = file("templates/visualization.json.tpl")

  vars = {
    vis_container_name   = "visualization"
    docker_image_url_vis = "vasilis421/r-vis-api:latest"
    vis_container_cpu    = 128
    vis_container_memory = 256
    vis_container_port   = 80
    vis_host_port        = 8006
    region               = var.region
  }
}

resource "aws_ecs_task_definition" "visualization" {
  family                = "visualization"
  container_definitions = data.template_file.vis.rendered
  network_mode          = "bridge"
}

resource "aws_ecs_service" "visualization" {
  name                   = "vis-service"
  cluster                = aws_ecs_cluster.backend-cluster.id
  task_definition        = aws_ecs_task_definition.visualization.arn
  iam_role               = aws_iam_role.scenariodt-service-role.arn
  desired_count          = var.vis_count
  depends_on             = [aws_alb_listener_rule.vis, aws_iam_role_policy.scenariodt-service-role-policy]
  
  load_balancer {
    target_group_arn = aws_alb_target_group.vis-target-group.arn
    container_name   = "visualization"
    container_port   = 80
  }
}