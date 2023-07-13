resource "aws_cloudwatch_log_group" "fuseki-log-group" {
  name              = "/ecs/fuseki"
  retention_in_days = var.log_retention_in_days
}

resource "aws_cloudwatch_log_stream" "fuseki-log-stream" {
  name           = "fuseki-log-stream"
  log_group_name = aws_cloudwatch_log_group.fuseki-log-group.name
}