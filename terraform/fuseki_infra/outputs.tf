output "fuseki_instance_ip" {
  value = aws_instance.fuseki_instance.public_ip
}