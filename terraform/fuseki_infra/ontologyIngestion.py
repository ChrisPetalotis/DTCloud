import requests
from rdflib import Dataset, URIRef
import os
import boto3

s3_client = boto3.client('s3')
S3_BUCKET = 'scenario-dt-bucket'
S3_PREFIX = 'Ontologies/'

def lambda_handler(event, context):
    
    host = os.getenv("EC2_PUBLIC_IP")
    endpoint_update = f"http://{host}:3030/ds/update"
    endpoint_query = f"http://{host}:3030/ds/sparql"
    
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint_query, endpoint_update))
    ds.remove_graph(ds.get_context(URIRef("http://www.myapp.org/ontology")))

    fuseki_url = f"http://{host}:3030/ds/"  # Replace with your Fuseki server URL
    graph_name = "ontology"
    ontologies = ["ontoGeo", "ontoEco", "ontoDomain", "ontoScenario", "ontoFlow", "ontoContainer", "ontoDeploy"]
    headers = {"Content-Type": "text/turtle"}
    for ontology in ontologies:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=f'Ontologies/{ontology}.ttl')
        file = response['Body'].read()
        response = requests.post(fuseki_url+"data?graph=http://www.myapp.org/"+graph_name, headers=headers, data=file)
    return {
        'statusCode': 200,
    }