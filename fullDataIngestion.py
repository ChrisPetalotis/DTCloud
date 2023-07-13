from rdflib import Namespace
import domainDataIngestion as domain
import serviceDataIngestion as service
import containerDataIngestion as container
import InfraDataIngestion as infra


DOCKER = Namespace("https://w3.org/ns/bde/docker#")
MYAPP = Namespace("http://www.myapp.org/")
ontoContainer = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/")
ontoFlow = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoFlow/")


host = "localhost"
endpoint = f"http://{host}:3030/ds/"
filepath = 'G:/My Drive/Thesis/GrW_observation.csv'

domain.dataIngestionBasedOnOntology(endpoint, filepath)
service.ingestServices(endpoint)
container.ingestContainers(endpoint)
infra.ingestInfra(endpoint, 'db')
infra.ingestInfra(endpoint, 'scenariodt_infra')




