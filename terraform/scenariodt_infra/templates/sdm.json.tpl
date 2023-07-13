[
  {
    "name":"${sdm_container_name}",
    "image": "${docker_image_url_sdm}",
    "essential": true,
    "cpu": ${sdm_container_cpu},
    "memoryReservation": ${sdm_container_memory},
    "links": [],
    "portMappings": [
      {
        "containerPort": ${sdm_container_port},
        "hostPort": ${sdm_host_port},
        "protocol": "tcp"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/${sdm_container_name}",
        "awslogs-region": "${region}",
        "awslogs-stream-prefix": "${sdm_container_name}-log-stream"
      }
    }
  }
]