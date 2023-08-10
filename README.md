# A Knowledge Graph enhanced framework for automation and collaboration in Digital Twins

## Computational Science Master Thesis on Digital Twins and Cloud Computing

The 'app' folder includes the Django project for EcoDTwin, a What-if Analysis DT service, where users can configure, execute, compare, and share scenarios.

The 'SDM' folder includes the R code (based on https://github.com/komazsofi/LiDAR_Sentinel_birdsdm_wetlands) for the Simulation service, which is developed a an plumber API.

The 'Visualization' folder includes the R code for the Visualization service, which is developed as a plumber API.

The 'nginx' folder includes the configuration of the nginx web-server, which servers the django static files.

Every service is containerized, with its own custom Dockerfile or existing Docker image. The docker-compose.yml can be used to run the stack locally, including the django container, the nginx container, the simulation and visualization containers, the Apache Jena-Fuseki container (Knowledge Base), and a mysql user db container.

The folders fuseki-configuration and fuseki-data are required by the fuseki container image (https://hub.docker.com/r/secoresearch/fuseki/), for the triplestore configuration and for persistent storage.

The terraform folder includes the IaC scripts for the provision of AWS infrastructure for the fuseki triplestore, the user db, and the rest of the DT services. They must be applied in this order: fuseki_infra -> db -> scenariodt_infra. By deploying Fuseki, an AWS Lambda function is triggered that ingests the ontologies in the Knowledge Base.

The Ontologies folder includes the developed ontologies in turtle format.

The Data folder includes data for the wetlands ecosystem use case, such as vegetation metrics and bird observations (https://zenodo.org/record/6497349#.Y8AmYxXMKUn , https://zenodo.org/record/5772673#.Y8AmMBXMKUl).

After the containers are running, the data ingestion python scripts can be run to ingest data to Fuseki in the following order: domainDataIngestion.py, serviceDataIngestion.py, containerDataIngestion.py, infraDataIngestion.py (or just fullDataIngestion.py). Currently, localhost is used for the Fuseki endpoint. If Fuseki is deployed on AWS, the public IP of the EC2 instance that hosts Fuseki must replace localhost in the data ingestion scripts.

The files mappingAgents.py and queryAgents.py include custom algorithms that are imported and used by the rest of the project.

dockerizeDT.py can be used to automate the process of generating the Dockerfiles and the docker-compose.yml for the DT services, after container data have been ingested in the Knowledge Base.

automatedDeployment.py can be used to automate the generation of the ECS related terraform script for the DT services by rendering a Jinja template, after container data have been ingested in the Knowledge Base, and finally deploy the services to AWS. Fuseki and User DB must be already deployed.