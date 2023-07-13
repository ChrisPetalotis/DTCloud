output "alb_hostname" {
  value = aws_lb.scenariodt-load-balancer.dns_name
}