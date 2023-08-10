from rdflib import Namespace
import domainDataIngestion as domain
import serviceDataIngestion as service
import containerDataIngestion as container
import infraDataIngestion as infra
import time


DOCKER = Namespace("https://w3.org/ns/bde/docker#")
MYAPP = Namespace("http://www.myapp.org/")
ontoContainer = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/")
ontoFlow = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoFlow/")


host = "localhost"
endpoint = f"http://{host}:3030/ds/"
filepath = './Data/GrW_observation.csv'

domainStart = time.time()
domain.dataIngestionBasedOnOntology(endpoint, filepath)
domainEnd = time.time()
service.ingestServices(endpoint)
serviceEnd = time.time()
container.ingestContainers(endpoint)
containerEnd = time.time()
infra.ingestInfra(endpoint, 'db')
infra.ingestInfra(endpoint, 'scenariodt_infra')
infraEnd = time.time()

print('Domain Data Ingestion: ', domainEnd - domainStart)
print('Service Data Ingestion: ', serviceEnd - domainEnd)
print('Container Data Ingestion: ', containerEnd - serviceEnd)
print('Infra Data Ingestion: ', infraEnd - containerEnd)
print('-----------------------------------')
print('Full Data Ingestion: ', infraEnd - domainStart)




