resource "aws_cloudwatch_log_group" "scenariodt-log-group" {
  name              = "/ecs/scenario_dt"
  retention_in_days = var.log_retention_in_days
}

resource "aws_cloudwatch_log_stream" "scenariodt-log-stream" {
  name           = "scenario_dt-log-stream"
  log_group_name = aws_cloudwatch_log_group.scenariodt-log-group.name
}

resource "aws_cloudwatch_log_group" "nginx-log-group" {
  name              = "/ecs/nginx"
  retention_in_days = var.log_retention_in_days
}

resource "aws_cloudwatch_log_stream" "nginx-log-stream" {
  name           = "nginx-log-stream"
  log_group_name = aws_cloudwatch_log_group.nginx-log-group.name
}

resource "aws_cloudwatch_log_group" "sdm-log-group" {
  name              = "/ecs/sdm"
  retention_in_days = var.log_retention_in_days
}

resource "aws_cloudwatch_log_stream" "sdm-log-stream" {
  name           = "sdm-log-stream"
  log_group_name = aws_cloudwatch_log_group.sdm-log-group.name
}

resource "aws_cloudwatch_log_group" "vis-log-group" {
  name              = "/ecs/visualization"
  retention_in_days = var.log_retention_in_days
}

resource "aws_cloudwatch_log_stream" "vis-log-stream" {
  name           = "visualization-log-stream"
  log_group_name = aws_cloudwatch_log_group.vis-log-group.name
}