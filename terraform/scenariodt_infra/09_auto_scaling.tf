resource "aws_autoscaling_group" "scenariodt-ecs-cluster" {
  name                 = "${var.ecs_cluster_name}_auto_scaling_group"
  min_size             = var.autoscale_min
  max_size             = var.autoscale_max
  health_check_type    = "EC2"
  launch_configuration = aws_launch_configuration.ecs.name
  vpc_zone_identifier  = ["${data.terraform_remote_state.db.outputs.public_subnet_1_id}", "${data.terraform_remote_state.db.outputs.public_subnet_2_id}"]
}

resource "aws_autoscaling_group" "backend-cluster" {
  name                 = "${var.backend_cluster_name}_auto_scaling_group"
  min_size             = var.backend_autoscale_min
  max_size             = var.backend_autoscale_max
  health_check_type    = "EC2"
  launch_configuration = aws_launch_configuration.backend.name
  vpc_zone_identifier  = ["${data.terraform_remote_state.db.outputs.public_subnet_1_id}", "${data.terraform_remote_state.db.outputs.public_subnet_2_id}"]
}

resource "aws_autoscaling_policy" "scenariodt_cpu_policy" {
  name                   = "scenariodt-policy-cpu"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.scenariodt-ecs-cluster.name

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 90.0
  }
}

resource "aws_autoscaling_policy" "backend_cpu_policy" {
  name                   = "backend-policy-cpu"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.backend-cluster.name

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 90.0
  }
}

# ECS Service Scaling

resource "aws_appautoscaling_target" "scenariodt_service" {
  max_capacity       = 5
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.scenariodt-cluster.name}/${aws_ecs_service.scenariodt.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "scenariodt_service_cpu_policy" {
  name               = "scenariodt-target-tracking-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.scenariodt_service.resource_id
  scalable_dimension = aws_appautoscaling_target.scenariodt_service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.scenariodt_service.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 90.0
  }
}


resource "aws_appautoscaling_target" "sdm_service" {
  max_capacity       = 7
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.backend-cluster.name}/${aws_ecs_service.sdm.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "sdm_service_cpu_policy" {
  name               = "sdm-target-tracking-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.sdm_service.resource_id
  scalable_dimension = aws_appautoscaling_target.sdm_service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sdm_service.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 90.0
  }
}


resource "aws_appautoscaling_target" "vis_service" {
  max_capacity       = 5
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.backend-cluster.name}/${aws_ecs_service.visualization.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "vis_service_cpu_policy" {
  name               = "vis-target-tracking-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.vis_service.resource_id
  scalable_dimension = aws_appautoscaling_target.vis_service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.vis_service.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 90.0
  }
}

resource "aws_appautoscaling_policy" "scenariodt_service_memory_policy" {
  name               = "scenariodt-target-tracking-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.scenariodt_service.resource_id
  scalable_dimension = aws_appautoscaling_target.scenariodt_service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.scenariodt_service.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 90.0
  }
}
resource "aws_appautoscaling_policy" "sdm_service_memory_policy" {
  name               = "sdm-target-tracking-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.sdm_service.resource_id
  scalable_dimension = aws_appautoscaling_target.sdm_service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sdm_service.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 90.0
  }
}
resource "aws_appautoscaling_policy" "vis_service_memory_policy" {
  name               = "vis-target-tracking-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.vis_service.resource_id
  scalable_dimension = aws_appautoscaling_target.vis_service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.vis_service.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 90.0
  }
}