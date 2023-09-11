import os
from django.contrib import messages
from rdflib import Dataset

from celery import shared_task
from . import views

endpoint = os.getenv('SPARQL_ENDPOINT', "http://fuseki:3030/") + "ds/"
endpoint_update = endpoint + "update"
endpoint_query = endpoint + "sparql"

SDM_endpoint = os.getenv('SDM_ENDPOINT', 'http://sdm:80/')

@shared_task
def handle_scenario_execution(scenario_name, used_id):

    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    # create named graph for the scenario to save the updated values
    views.createScenarioView(ds, scenario_name, used_id)
    # retrieve scenario RDF data and transform to pandas dataframe
    df = views.RDFtoDataFrame(ds, scenario_name)
    # send data to SDM API and get predictions
    predictions = views.getSDMResults(df, SDM_endpoint)
    # transform predictions to RDF and save to sfcenario named graph
    views.addResultsToGraph(ds, scenario_name, predictions)
    # messages.add_message(request, messages.INFO, "Results were saved to scenario view.")
