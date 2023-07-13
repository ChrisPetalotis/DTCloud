resource "aws_key_pair" "scenariodt-kp" {
  key_name   = "${var.ecs_cluster_name}_key_pair"
  public_key = file(var.ssh_pubkey_file)
}

resource "aws_key_pair" "backend-kp" {
  key_name   = "backend_key_pair"
  public_key = file(var.backend_ssh_pubkey_file)
}