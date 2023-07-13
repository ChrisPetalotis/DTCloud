resource "aws_iam_role" "ecs-host-role" {
  name               = "ecs_host_role_prod"
  assume_role_policy = file("policies/ecs-role.json")
}

resource "aws_iam_role_policy" "ecs-instance-role-policy" {
  name   = "ecs_instance_role_policy"
  policy = file("policies/ecs-instance-role-policy.json")
  role   = aws_iam_role.ecs-host-role.id
}

resource "aws_iam_role_policy_attachment" "ecs_instance_role_policy_attachment" {
  role       = aws_iam_role.ecs-host-role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_instance_profile" "ecs" {
  name = "ecs_instance_profile_prod"
  path = "/"
  role = aws_iam_role.ecs-host-role.name
}

# lambda

resource "aws_iam_role" "fuseki-lambda-role" {
  name               = "fuseki_lambda_role"
  assume_role_policy = file("policies/lambda-role.json")
}

resource "aws_iam_role_policy" "lambda-role-policy" {
  name   = "ecs_instance_role_policy"
  policy = file("policies/lambda-role-policy.json")
  role   = aws_iam_role.fuseki-lambda-role.id
}

