from django.apps import AppConfig
from rdflib import Dataset
import os

endpoint = os.environ.get('SPARQL_ENDPOINT', "http://fuseki:3030/") + "ds/"
endpoint_update = endpoint + "update"
endpoint_query = endpoint + "sparql"

def warm_up_fuseki_connection():
    # Perform a lightweight initialization request to Fuseki
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    sparql = """
          PREFIX myapp: <http://www.myapp.org/>
          PREFIX ssn: <http://www.w3.org/ns/ssn/>
          PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
          PREFIX envo: <http://purl.obolibrary.org/obo/ENVO_>
          SELECT DISTINCT ?m ?lab1 ?l ?lab2
          WHERE {
              {GRAPH myapp:ontology {
                ?m rdfs:subClassOf* ssn:Property ;
                   rdfs:label ?lab1 .
                FILTER NOT EXISTS {?s rdfs:subClassOf ?m}
              }
              }
              UNION
              {GRAPH myapp:ecosystem {
                ?l a ?landcover .
                FILTER regex(str(?l), "No0")
              }
              GRAPH myapp:ontology {
                ?landcover rdfs:subClassOf* envo:00000043 ;
                           rdfs:label ?lab2 .
                FILTER NOT EXISTS {?o rdfs:subClassOf ?landcover}
              }
              } 
          }"""
    results = ds.query(sparql)

class ScenariodtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scenariodt'

    '''def ready(self):
        # Call the warm-up function during application startup
        warm_up_fuseki_connection()'''
