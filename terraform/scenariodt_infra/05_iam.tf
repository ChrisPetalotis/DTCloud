resource "aws_iam_role" "scenariodt-host-role" {
  name               = "ecs_host_role_scenariodt"
  assume_role_policy = file("policies/ecs-role.json")
}

resource "aws_iam_role_policy" "scenariodt-instance-role-policy" {
  name   = "scenariodt_instance_role_policy"
  policy = file("policies/ecs-instance-role-policy.json")
  role   = aws_iam_role.scenariodt-host-role.id
}

resource "aws_iam_role" "scenariodt-service-role" {
  name               = "scenariodt_service_role_prod"
  assume_role_policy = file("policies/ecs-role.json")
}

resource "aws_iam_role_policy" "scenariodt-service-role-policy" {
  name   = "scenariodt_service_role_policy"
  policy = file("policies/ecs-service-role-policy.json")
  role   = aws_iam_role.scenariodt-service-role.id
}

resource "aws_iam_role_policy_attachment" "scenariodt_instance_role_policy_attachment" {
  role       = aws_iam_role.scenariodt-host-role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_instance_profile" "scenariodt" {
  name = "ecs_instance_profile_scenariodt"
  path = "/"
  role = aws_iam_role.scenariodt-host-role.name
}



resource "aws_iam_role" "ecs-autoscale-role" {
  name = "ecs-scale-application"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "application-autoscaling.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs-autoscale" {
  role = aws_iam_role.ecs-autoscale-role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceAutoscaleRole"
}