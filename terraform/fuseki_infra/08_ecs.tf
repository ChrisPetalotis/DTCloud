# FUSEKI CLUSTER
resource "aws_ecs_cluster" "fuseki-cluster" {
  name = "${var.fuseki_ecs_cluster_name}-cluster"
}

resource "aws_key_pair" "fuseki-kp" {
  key_name   = "${var.fuseki_ecs_cluster_name}_key_pair"
  public_key = file(var.fuseki_ssh_pubkey_file)
}

resource "aws_instance" "fuseki_instance" {
  ami                         = var.ami
  security_groups             = [aws_security_group.fuseki-ecs-sg.id]
  subnet_id                   = aws_subnet.fuseki-public-subnet-1.id
  instance_type               = var.instance_type
  iam_instance_profile        = aws_iam_instance_profile.ecs.name
  key_name                    = aws_key_pair.fuseki-kp.key_name
  associate_public_ip_address = true
  monitoring                  = false
  user_data                   = "#!/bin/bash\necho ECS_CLUSTER='${var.fuseki_ecs_cluster_name}-cluster' >> /etc/ecs/ecs.config"
  depends_on                  = [aws_internet_gateway.fuseki-igw]
  tags = {
    Name = "FusekiServer"
  }
}

data "template_file" "fuseki" {
  template = file("templates/fuseki.json.tpl")

  vars = {
    docker_image_url_fuseki = var.docker_image_url_fuseki
    region                  = var.region
    fuseki_pwd              = var.fuseki_pwd
    fuseki_timeout          = var.fuseki_timeout
  }
}

resource "aws_ecs_task_definition" "fuseki" {
  family                = "fuseki"
  container_definitions = data.template_file.fuseki.rendered
  network_mode          = "bridge"
}

resource "aws_ecs_service" "fuseki" {
  name                   = "${var.fuseki_ecs_cluster_name}-service"
  cluster                = aws_ecs_cluster.fuseki-cluster.id
  task_definition        = aws_ecs_task_definition.fuseki.arn
  desired_count          = var.fuseki_count
}