provider "archive" {}
data "archive_file" "zip" {
  type        = "zip"
  source_file = "ontologyIngestion.py"
  output_path = "ontologyIngestion.zip"
}

resource "aws_lambda_function" "ontology_ingestion" {
  function_name    = "ontology_ingestion"
  filename         = data.archive_file.zip.output_path
  source_code_hash = data.archive_file.zip.output_base64sha256
  role             = aws_iam_role.fuseki-lambda-role.arn
  handler          = "ontologyIngestion.lambda_handler"
  runtime          = "python3.8"
  layers           = ["arn:aws:lambda:eu-central-1:150304539074:layer:requests:1", "arn:aws:lambda:eu-central-1:150304539074:layer:rdflib:4"]

  environment {
    variables = {
      EC2_PUBLIC_IP = aws_instance.fuseki_instance.public_ip
    }
  }
}

resource "aws_cloudwatch_event_rule" "ec2_launch_event_rule" {
  name        = "ec2_launch_event_rule"
  description = "Trigger Lambda when Fuseki is running"
  event_pattern = <<PATTERN
{
  "detail-type": ["ECS Task State Change"],
  "source": ["aws.ecs"],
  "detail": {
    "taskDefinitionArn": [{
      "prefix": "${aws_ecs_task_definition.fuseki.arn}"
    }],
    "lastStatus": ["RUNNING"]
  }
}
PATTERN
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.ec2_launch_event_rule.name
  arn       = aws_lambda_function.ontology_ingestion.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_event_exec" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ontology_ingestion.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_launch_event_rule.arn
}