[
  {
    "name": "fuseki",
    "image": "${docker_image_url_fuseki}",
    "essential": true,
    "cpu": 512,
    "memory": 512,
    "links": [],
    "environment": [
      {
        "name": "ADMIN_PASSWORD",
        "value": "${fuseki_pwd}"
      },
      {
        "name": "ENABLE_DATA_WRITE",
        "value": "true"
      },
      {
        "name": "ENABLE_UPDATE",
        "value": "true"
      },
      {
        "name": "ENABLE_UPLOAD",
        "value": "true"
      },
      {
        "name": "QUERY_TIMEOUT",
        "value": "${fuseki_timeout}"
      }
    ],
    "portMappings": [
      {
        "containerPort": 3030,
        "hostPort": 3030
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/fuseki",
        "awslogs-region": "${region}",
        "awslogs-stream-prefix": "fuseki-log-stream"
      }
    }
  }
]