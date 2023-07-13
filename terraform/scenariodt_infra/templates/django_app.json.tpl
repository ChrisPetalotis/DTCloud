[
  {
    "name": "${django_container_name}",
    "image": "${docker_image_url_django}",
    "essential": true,
    "cpu": ${django_container_cpu},
    "memory": ${django_container_memory},
    "links": [],
    "portMappings": [
      {
        "containerPort": ${django_container_port},
        "hostPort": ${django_host_port},
        "protocol": "tcp"
      }
    ],
    "command": [
      "sh",
      "-c",
      "${django_command}"
    ],
    "environment": [
      {
        "name": "RDS_DB_NAME",
        "value": "${rds_db_name}"
      },
      {
        "name": "RDS_USERNAME",
        "value": "${rds_username}"
      },
      {
        "name": "RDS_PASSWORD",
        "value": "${rds_password}"
      },
      {
        "name": "RDS_HOSTNAME",
        "value": "${rds_hostname}"
      },
      {
        "name": "RDS_PORT",
        "value": "${rds_port}"
      },
      {
        "name": "AWS_ACCESS_KEY_ID",
        "value": "${aws_access_key}"
      },
      {
        "name": "AWS_SECRET_ACCESS_KEY",
        "value": "${aws_secret_key}"
      },
      {
        "name": "S3",
        "value": "True"
      },
      {
        "name": "DEBUG",
        "value": "False"
      },
      {
        "name": "SPARQL_ENDPOINT",
        "value": "http://${sparql_endpoint}:3030/"
      },
      {
        "name": "SDM_ENDPOINT",
        "value": "http://${sdm_endpoint}/"
      },
      {
        "name": "VIS_ENDPOINT",
        "value": "http://${vis_endpoint}/"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/${django_container_name}",
        "awslogs-region": "${region}",
        "awslogs-stream-prefix": "${django_container_name}-log-stream"
      }
    }
  },
  {
    "name":"${nginx_container_name}",
    "image": "${docker_image_url_nginx}",
    "essential": true,
    "cpu": ${nginx_container_cpu},
    "memory": ${nginx_container_memory},
    "links": ["${django_container_name}"],
    "portMappings": [
      {
        "containerPort": ${nginx_container_port},
        "hostPort": ${nginx_host_port},
        "protocol": "tcp"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/${nginx_container_name}",
        "awslogs-region": "${region}",
        "awslogs-stream-prefix": "${nginx_container_name}-log-stream"
      }
    }
  }
]