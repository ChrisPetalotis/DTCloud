[
  {
    "name":"${vis_container_name}",
    "image": "${docker_image_url_vis}",
    "essential": true,
    "cpu": ${vis_container_cpu},
    "memoryReservation": ${vis_container_memory},
    "links": [],
    "portMappings": [
      {
        "containerPort": ${vis_container_port},
        "hostPort": ${vis_host_port},
        "protocol": "tcp"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/${vis_container_name}",
        "awslogs-region": "${region}",
        "awslogs-stream-prefix": "${vis_container_name}-log-stream"
      }
    }
  }
]