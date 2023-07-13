from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import queryAgents as qa


host = '18.198.209.204'
endpoint = f"http://{host}:3030/ds/"


# Retrieve the container details from the knowledge graph
print('Retrieving container details from the knowledge base...')
containers = qa.getContainers(endpoint)
for c in containers:
    if 'scenario' in str(c[1]):
        django_container_name = str(c[1])
    elif 'nginx' in str(c[1]):
        nginx_container_name = str(c[1])
    elif 'sdm' in str(c[1]):
        simulation_container_name = str(c[1])
    elif 'visualization' in str(c[1]):
        visualization_container_name = str(c[1])

django_image = qa.getContainerImage(endpoint, [django_container_name])
for i in django_image:
    django_image = str(i[0])
nginx_image = qa.getContainerImage(endpoint, [nginx_container_name])
for i in nginx_image:
    nginx_image = str(i[0])
simulation_image = qa.getContainerImage(endpoint, [simulation_container_name])
for i in simulation_image:
    simulation_image = str(i[0])
visualization_image = qa.getContainerImage(endpoint, [visualization_container_name])
for i in visualization_image:
    visualization_image = str(i[0])

django_command = qa.getContainerCmd(endpoint, [django_container_name])
for c in django_command:
    django_command = str(c[0]).split(' -c ')[-1]

django_ports = qa.getContainerPorts(endpoint, [django_container_name])
for p in django_ports:
    django_container_port = str(p[0])
    django_host_port = str(p[1])

nginx_ports = qa.getContainerPorts(endpoint, [nginx_container_name])
for p in nginx_ports:
    nginx_container_port = str(p[0])
    nginx_host_port = str(p[1])

simulation_ports = qa.getContainerPorts(endpoint, [simulation_container_name])
for p in simulation_ports:
    simulation_container_port = str(p[0])
    simulation_host_port = str(p[1])

visualization_ports = qa.getContainerPorts(endpoint, [visualization_container_name])
for p in visualization_ports:
    visualization_container_port = str(p[0])
    visualization_host_port = str(p[1])


# Fill in the Jinja2 template with the values retrieved from the knowledge graph
print('Generating the ECS Terraform template...')
env = Environment(loader=FileSystemLoader('jinjaTemplates'))
ecs_template = env.get_template('08_ecs.j2')
ecs = ecs_template.render(
    django_container_name=django_container_name,
    django_image = django_image,
    django_command = django_command,
    django_container_port = django_container_port,
    django_host_port = django_host_port,
    nginx_container_name = nginx_container_name,
    nginx_image = nginx_image,
    nginx_container_port = nginx_container_port,
    nginx_host_port = nginx_host_port,
    simulation_container_name = simulation_container_name,
    simulation_image = simulation_image,
    simulation_container_port = simulation_container_port,
    simulation_host_port = simulation_host_port,
    visualization_container_name = visualization_container_name,
    visualization_image = visualization_image,
    visualization_container_port = visualization_container_port,
    visualization_host_port = visualization_host_port,
)

# Generate the ECS Terraform file
with open('./terraform/scenariodt_infra/08_ecs.tf', "w") as f:
    f.write(ecs)

# Deploy
print('Deploying to AWS:')
current_dir = os.getcwd()
os.chdir('./terraform/scenariodt_infra')
terraform_cmd = ["terraform", "apply", "-auto-approve"]
subprocess.run(terraform_cmd, check=True)
os.chdir(current_dir)