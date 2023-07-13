from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.forms import UserCreationForm
from django.templatetags.static import static
from .forms import *
from django.contrib.auth import logout as dlogout
from datetime import datetime
from rdflib import URIRef, Graph, Literal, Namespace, Dataset
from shapely.geometry import Point, Polygon
import re
from django.contrib.gis.geos import GEOSGeometry
import pyproj
import pandas as pd
import requests
import json
import base64
import os

import dash_cytoscape as cyto
from dash import html, dcc
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

GML = Namespace("http://www.opengis.net/gml/3.2/")
MYAPP = Namespace("http://www.myapp.org/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
ENVO = Namespace("http://purl.obolibrary.org/obo/ENVO_")
ECSO = Namespace("http://www.purl.dataone.org/odo/ECSO_")
RO = Namespace("http://purl.obolibrary.org/obo/RO_")
SIO = Namespace("http://semanticscience.org/resource/SIO_")
SNOMED = Namespace("http://snomed.info/id/")
SSN = Namespace("http://www.w3.org/ns/ssn/")
GEOSPARQL = Namespace("http://www.opengis.net/ont/geosparql#")
NCIT = Namespace("http://purl.obolibrary.org/obo/NCIT_")
BFO = Namespace("http://purl.obolibrary.org/obo/BFO_")
PROV = Namespace("http://www.w3.org/ns/prov#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
ontoGeo = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoGeo/")
ontoEco = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoEco/")
ontoScenario = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/")

sio_ = {'has value':'000300', 'has property': '000223', 'has part': '000028'}
bfo_ = {'has part':'0000051', 'occurs in':'0000066'}
envo_ = {'ecosystem':'01001110', 'ecoregion':'01000276', 'wetland':'00000043', 'swamp forest':'01000432', 'shrub layer':'01000336', 'shrub area':'01000869', 'dwarf shrub area': '01000861', 'saline marsh': '00000054',
                    'swamp ecosystem':'00000233', 'swamp area':'01001208', 'wetland forest':'01000893', 'habitat':'01000739'}
ro_ = {'has characteristic':'0000053', 'contained in':'0001018', 'has habitat':'0002303', 'visits':'0002618', 'overlaps':'0002131'}
ecso_ = {'ndvi':'00010076'}
snomed = {'great reed warbler':'49532004', 'occurrence':'246454002'}

endpoint = os.getenv('SPARQL_ENDPOINT', "http://fuseki:3030/") + "ds/"
endpoint_update = endpoint + "update"
endpoint_query = endpoint + "sparql"

SDM_endpoint = os.getenv('SDM_ENDPOINT', 'http://sdm:80/')
vis_endpoint = os.getenv('VIS_ENDPOINT', 'http://visualization:80/')

def main(request):
    ''' Shows home / main page.'''
    return render(request, "main.html")

def register(request):
    '''Register view'''
    if request.user.is_authenticated:
        return redirect("main")

    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        if user_form.is_valid():
            user_form.save()
            cache.clear()
            messages.success(request, 'Account created successfully.')
            return redirect('main')
    else:
        user_form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': user_form})

def profile(request):
    '''Profile view'''
    return redirect('main')

def logout(request):
    '''Logout view'''
    dlogout(request)
    return redirect('main')

def configureScenario(request):
    '''Configure scenario view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    return render(request, 'configure_scenario.html')

def configureNewScenario(request):
    '''New scenario view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    
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
    options = []
    for row in results:
        if row[0] != None:
            options.append((row[0].rsplit("/", 1)[-1], str(row[1]) + " (" + str(row[0].rsplit("/", 1)[-1]) + ")"))
        else:
            options.append((row[2].rsplit("/", 1)[-1].rsplit("_", 1)[0], "Fraction of " + str(row[3]) + " Area"))
    if request.method == 'POST':
        form = ScenarioConfigForm(options, request.POST)
        if form.is_valid():
            condition = form.cleaned_data['scenario_condition']
            description = form.cleaned_data['scenario_description']
            region = request.POST['scenario_region']
            factors = form.cleaned_data['impact_factors']
            # Save the scenario configuration to the database
            storeScenario(request.user, ds, condition, description, region, factors)
            # Redirect to a success page or do something else
            messages.add_message(request, messages.INFO, "Scenario configuration saved successfully.")
            return redirect("main")
    else:
        form = ScenarioConfigForm(options)

    return render(request, 'new_scenario.html', {'sform': form})

def selectScenario(request):
    '''Select scenario view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    sparql = """
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX prov: <http://www.w3.org/ns/prov#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX ontoScenario: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/>
                SELECT DISTINCT ?scenario ?name
                WHERE 
                {{
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name ;
                            prov:wasAttributedTo myapp:user_{user} .
                        }}
                    }}
                    UNION
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name .
                        myapp:user_{user} ontoScenario:hasAccess ?scenario .
                        }}
                    }}
                }}""".format(user=str(request.user.id))
    results = ds.query(sparql)
    
    options=[]
    for row in results:
        options.append((row[0], row[1]))

    if request.method == 'POST':
        form = ScenarioSelectionForm(options, request.POST)
        if form.is_valid():
            scenario = request.POST['scenario']
            request.session['scenario'] = scenario
            return redirect('reconfigure_scenario')
    else:
        form = ScenarioSelectionForm(options)

    return render(request, 'select_scenario.html', {'selectform': form})

def reconfigureScenario(request):
    '''Reconfigure scenario view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    sparql = """
          PREFIX myapp: <http://www.myapp.org/>
          PREFIX sio: <http://semanticscience.org/resource/SIO_>
          PREFIX ssn: <http://www.w3.org/ns/ssn/>
          PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
          PREFIX envo: <http://purl.obolibrary.org/obo/ENVO_>
          SELECT DISTINCT ?m ?lab1 ?l ?lab2
          WHERE {
              {GRAPH myapp:ontology {
                ?m rdfs:subClassOf* ssn:Property ;
                   rdfs:label ?lab1 .
                FILTER NOT EXISTS {?s rdfs:subClassOf ?m}
              }}
              UNION
              {GRAPH myapp:ecosystem {
                ?l a ?landcover .
                FILTER regex(str(?l), "No0")
              }
              GRAPH myapp:ontology {
                ?landcover rdfs:subClassOf* envo:00000043 ;
                           rdfs:label ?lab2 .
                FILTER NOT EXISTS {?o rdfs:subClassOf ?landcover}
              }}
              
          }

          """
    results = ds.query(sparql)
    options = {}
    for row in results:
        if row[0] != None:
            options[row[0].rsplit("/", 1)[-1]] = str(row[1]) + " (" + str(row[0].rsplit("/", 1)[-1]) + ")"
        else:
            options[row[2].rsplit("/", 1)[-1].rsplit("_", 1)[0]] = "Fraction of " + str(row[3]) + " Area"

    scenario = request.session.get('scenario')
    sparql2 = """
            PREFIX prov: <http://www.w3.org/ns/prov#>
            PREFIX myapp: <http://www.myapp.org/>
            PREFIX geo: <http://www.opengis.net/ont/geosparql#>
            PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX ontoScenario: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/>
            SELECT ?roiWKT ?condition ?description ?parameter ?factor
            WHERE {{
            {{GRAPH myapp:scenario {{
                <{scenario}> bfo:0000066 ?roi ;
                ontoScenario:hasScenarioCondition ?cond ;
                ontoScenario:hasScenarioDescription ?desc .
                ?cond prov:value ?condition .
                ?desc prov:value ?description .
                ?roi geo:hasGeometry ?geom .
                ?geom geo:asWKT ?roiWKT .
            }}}}
            UNION {{
            {{GRAPH myapp:scenario {{
                <{scenario}> ontoScenario:hasScenarioParameter ?param .
                ?param rdfs:label ?parameter .
                ?e ontoScenario:affects ?param .
                ?e ontoScenario:hasImpactFactor ?factor .
        
            }}}}
            }}
            }}
            """.format(scenario=scenario)
    results2 = ds.query(sparql2)
    params = {}
    for row in results2:
        if row[0] != None:
            roi = str(row[0])
            condition = row[1]
            description = row[2]
        else:
            params[row[3].rsplit(": ", 1)[-1]] = str(row[4])

    initials = {'condition': condition, 'description': description, 'parameters': params}

    if request.method == 'POST':
        form = ScenarioReconfigForm(options, initials, request.POST)
        if form.is_valid():
            condition = form.cleaned_data['scenario_condition']
            description = form.cleaned_data['scenario_description']
            factors = form.cleaned_data['impact_factors']
            # Save the scenario configuration to the database
            storeScenario(request.user, ds, condition, description, roi, factors, scenario)
            # Redirect to a success page or do something else
            messages.add_message(request, messages.INFO, "Scenario configuration saved successfully.")
            return redirect("main")
    else:
        form = ScenarioReconfigForm(options, initials)

    return render(request, 'reconfigure_scenario.html', {'reform': form})

def storeScenario(user, ds, scenario_condition, scenario_description, region, metrics_factors_dict, baseScenario=None):
    '''Save scenario configuration to graph'''
    
    scenario_graph = ds.graph(URIRef("http://www.myapp.org/scenario"))
    current_dateTime = str(datetime.now())
    scenario_id = current_dateTime.replace(' ', '').replace('-', '').replace(':','').rsplit(".", 1)[0]
    scenario_name = scenario_condition.replace(' ', '_') + "_" + scenario_id
    
    # add the scenario semantics in the knowledge graph
    quads = []
    quads.append((MYAPP[scenario_name + '_scenario'], RDF.type, ontoScenario.DomainScenario, scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario'], RDFS.label, Literal(scenario_name, datatype=XSD.string), scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario_condition'], RDF.type, ontoScenario.ScenarioCondition, scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario_condition'], PROV.value, Literal(scenario_condition, datatype=XSD.string), scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario'], ontoScenario.hasScenarioCondition, MYAPP[scenario_name + '_scenario_condition'], scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario_description'], RDF.type, ontoScenario.ScenarioDescription, scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario'], ontoScenario.hasScenarioDescription, MYAPP[scenario_name + '_scenario_description'], scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario_description'], PROV.value, Literal(scenario_description, datatype=XSD.string), scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario_configuration'], RDF.type, ontoScenario.ScenarioConfiguration, scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario_configuration'], PROV.startedAtTime, Literal(current_dateTime, datatype=XSD.datetime), scenario_graph))
    quads.append((MYAPP['user_' + str(user.id)], RDF.type, ontoScenario.User, scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario'], PROV.wasGeneratedBy, MYAPP[scenario_name + '_scenario_configuration'], scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario'], PROV.wasAttributedTo, MYAPP['user_' + str(user.id)], scenario_graph))
    quads.append((MYAPP.scenarioConfigAgent, RDF.type, ontoScenario.ScenarioConfigurationAgent, scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario_configuration'], PROV.wasAssociatedWith, MYAPP.scenarioConfigAgent, scenario_graph))
    quads.append((MYAPP.scenarioConfigAgent, PROV.actedOnBehalfOf, MYAPP['user_' + str(user.id)], scenario_graph))
    if baseScenario != None:
        quads.append((MYAPP[scenario_name + '_scenario'], PROV.wasDerivedFrom, URIRef(baseScenario), scenario_graph))
    
    #scenario parameters are: Region of intetest polygon, affected metrics, and impact factors
    quads.append((MYAPP[scenario_name + '_roi'], RDF.type, ontoScenario.ScenarioRegion, scenario_graph))
    quads.append((MYAPP[scenario_name + '_roi'], RDFS.label, Literal("Scenario " + scenario_name + " Region of Impact", datatype=XSD.string), scenario_graph))
    quads.append((MYAPP[scenario_name + "_roi_geometry"], RDF.type, GML.Polygon, scenario_graph))
    quads.append((MYAPP[scenario_name + '_roi'], GEOSPARQL.hasGeometry, MYAPP[scenario_name + "_roi_geometry"], scenario_graph))
    if baseScenario == None:
        roi_coords = transformSRS(region)
        poslist = ""
        for coord in roi_coords:
            poslist += str(coord[0]) + " " + str(coord[1]) + ", "
        region = "POLYGON((" + poslist[:-2] + "))"
    quads.append((MYAPP[scenario_name + "_roi_geometry"], GEOSPARQL.asWKT, Literal(region, datatype=GEOSPARQL.wktLiteral), scenario_graph))
    quads.append((MYAPP[scenario_name + "_roi_geometry"], GML.srsName, Literal("urn:ogc:def:crs:EPSG::28992", datatype=XSD.string), scenario_graph))
    quads.append((MYAPP[scenario_name + '_scenario'], BFO[bfo_['occurs in']], MYAPP[scenario_name + '_roi'], scenario_graph))
    i = 0
    for metric, factor in metrics_factors_dict.items():
      i += 1
      if "landcover" in metric:
        if "forest" in metric:
            quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDF.type, ENVO[envo_['wetland forest']], scenario_graph))
        elif "shrub" in metric:
            if "high" in metric:
                quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDF.type, ENVO[envo_['shrub area']], scenario_graph))
            else:
                quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDF.type, ENVO[envo_['dwarf shrub area']], scenario_graph))
        elif "reed" in metric:
            quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDF.type, ontoEco['ReedArea'], scenario_graph))
        elif "marsh" in metric:
            quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDF.type, ENVO[envo_['saline marsh']], scenario_graph))
        elif "swamp" in metric:
            quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDF.type, ENVO[envo_['swamp area']], scenario_graph))
      else:
          quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDF.type, ontoEco[metric], scenario_graph))
      quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDF.type, ontoScenario.AffectedMetric, scenario_graph))
      quads.append((MYAPP[scenario_name + '_affected_metric_' + str(i)], RDFS.label, Literal("Scenario Parameter: " + metric, datatype=XSD.string), scenario_graph))
      quads.append((MYAPP[scenario_name + '_scenario'], ontoScenario.hasScenarioParameter, MYAPP[scenario_name + '_affected_metric_' + str(i)], scenario_graph))
      quads.append((MYAPP[scenario_name + '_effect_' + str(i)], RDF.type, ontoScenario.ScenarioEffect, scenario_graph))
      quads.append((MYAPP[scenario_name + '_effect_' + str(i)], RDFS.label, Literal("Scenario Effect on " + metric, datatype=XSD.string), scenario_graph))
      quads.append((MYAPP[scenario_name + '_effect_' + str(i)], ontoScenario.hasImpactFactor, Literal(factor, datatype=XSD.float), scenario_graph))
      quads.append((MYAPP[scenario_name + '_effect_' + str(i)], ontoScenario.affects, MYAPP[scenario_name + '_affected_metric_' + str(i)], scenario_graph))
    
    ds.addN(quads)

def transformSRS(region):
        # get region coordinates
        pattern = r'\[(-?\d+(\.\d+)?),(-?\d+(\.\d+)?)]'
        matches = re.findall(pattern, region)
        # Create a list of tuples with the coordinates
        coordinates = [(float(y), float(x)) for x, _, y, _ in matches]
        
        # transform coords to EPSG:28992
        src_crs = pyproj.CRS('EPSG:4326')
        target_crs = pyproj.CRS('EPSG:28992')
        transformer = pyproj.Transformer.from_crs(src_crs, target_crs)
        roi_coords = []
        for coord_pair in coordinates:
            x, y = transformer.transform(coord_pair[0], coord_pair[1])
            roi_coords.append((x, y))
        return roi_coords

def executeScenario(request):
    '''Submit scenario view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    sparql = """
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX prov: <http://www.w3.org/ns/prov#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX ontoScenario: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/>
                SELECT DISTINCT ?name
                WHERE 
                {{
                GRAPH ?g{{}}
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name ;
                            prov:wasAttributedTo myapp:user_{user} .
                        }}
                    }}
                    UNION
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name .
                        myapp:user_{user} ontoScenario:hasAccess ?scenario .
                        }}
                    }}
                    FILTER NOT EXISTS{{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario ontoScenario:wasExecutedBy ?exec .
                        }}
                    }}
                }}""".format(user=str(request.user.id))
    results = ds.query(sparql)
    options=[]
    for row in results:
            options.append((row[0], row[0]))
    if request.method == 'POST':
        form = ScenarioExecForm(options, request.POST)
        if form.is_valid():
            current_dateTime = str(datetime.now())
            scenario_name = request.POST['scenario']
            createScenarioView(ds, scenario_name, request.user)
            df = RDFtoDataFrame(ds, scenario_name)
            predictions = getSDMResults(df, SDM_endpoint)
            addResultsToGraph(ds, scenario_name, predictions)
            messages.add_message(request, messages.INFO, "Results were saved to scenario view.")
            results_df = retrieveScenarioResults(ds, scenario_name)
            img_url = getResultsVisualization(results_df, vis_endpoint)
            img_urls = {static('img/baseScenario.png'): 'Base Scenario'}
            img_urls[img_url] = scenario_name

            # Add scenario execution to graph
            scenario_graph = ds.graph(URIRef("http://www.myapp.org/scenario"))
            quads = []
            quads.append((MYAPP[scenario_name + '_scenario_execution'], RDF.type, ontoScenario.ScenarioExecution, scenario_graph))
            quads.append((MYAPP[scenario_name + '_scenario_execution'], PROV.startedAtTime, Literal(current_dateTime, datatype=XSD.datetime), scenario_graph))
            quads.append((MYAPP[scenario_name + '_scenario'], ontoScenario.wasExecutedBy, MYAPP[scenario_name + '_scenario_execution'], scenario_graph))
            ds.addN(quads)
            return render(request, "plot.html", {'scenario_img_urls': img_urls})
    else:
        form = ScenarioExecForm(options=options)

    return render(request, 'execute_scenario.html', {'eform': form})

def getSDMResults(output_df, API_url):
    json_data = '{"df":' + output_df.to_json() + '}'
    headers = {'Content-Type': 'application/json'}
    predictions = requests.post(API_url + "predictions", data=json_data, headers=headers)
    return json.loads(predictions.content)

def getResultsVisualization(df, API_url):
    json_data = '{"df":' + df.to_json() + '}'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(API_url + "plot", data=json_data, headers=headers)
    data_url = f"data:image/png;base64,{base64.b64encode(response.content).decode()}"
    return data_url

def createScenarioView(ds, scenario_name, user):
    """Function that accepts the region of interest geomerty in the form of long-lat pairs
    of the polygon, finds all the points within the region and their new values to the graph"""
    scenario_graph = ds.graph(URIRef("http://www.myapp.org/" + str(scenario_name)))
    #get the scenario region coordinates
    roi_sparql = """
              PREFIX myapp: <http://www.myapp.org/>
              PREFIX geo: <http://www.opengis.net/ont/geosparql#>
              PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
              PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
              PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
              SELECT ?roiWKT
              WHERE {{
                GRAPH myapp:scenario {{
                  ?scenario rdfs:label "{scenario}"^^xsd:string ;
                    bfo:0000066 ?roi .
                  ?roi geo:hasGeometry ?geom .
                  ?geom geo:asWKT ?roiWKT .
                }}
              }}""".format(scenario=scenario_name)
    roi = ds.query(roi_sparql)
    for row in roi:    
        coordinates=polygonToCoords(row[0])
    polygon = Polygon(coordinates)
    
    # get the points within the region and the rest of the scenario parameters
    sparql = """
              PREFIX myapp: <http://www.myapp.org/>
              PREFIX sio: <http://semanticscience.org/resource/SIO_>
              PREFIX geo: <http://www.opengis.net/ont/geosparql#>
              PREFIX ssn: <http://www.w3.org/ns/ssn/>
              PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
              PREFIX prov: <http://www.w3.org/ns/prov#>
              PREFIX ontoEco: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoEco/>
              PREFIX ontoScenario: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/>
              PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
              PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
              SELECT ?coords ?metric ?value ?f
              WHERE {{{{
                GRAPH myapp:ecosystem {{
                  ?obs a ontoEco:ObservationRegion ;
                    ssn:hasProperty ?metric ;
                    geo:hasCentroid ?point .
                  ?metric a ?metrictype ;
                    sio:000300 ?value .
                }}}}UNION{{
        		  GRAPH myapp:ecosystem {{
                  ?obs a ontoEco:ObservationRegion ;
                    bfo:0000051 ?metric ;
                    geo:hasCentroid ?point .
                  ?metric a ?metrictype ;
                   	ontoEco:coveredFractionOfRegion ?value .
      			}}
      			}}
                GRAPH myapp:map {{
                  ?point geo:asWKT ?coords .
                }}
                GRAPH myapp:scenario {{
                  ?scenario rdfs:label "{scenario}"^^xsd:string ;
                    bfo:0000066 ?roi ;
                    ontoScenario:hasScenarioParameter ?param ;
                    prov:wasAttributedTo myapp:user_{user} .
                  ?param a ?metrictype .
                  ?effect ontoScenario:affects ?param ;
                    ontoScenario:hasImpactFactor ?f .
                }}
              }}""".format(scenario=scenario_name, user=user.id)
    results = ds.query(sparql)
    quads = []
    for row in results:
        # get the coordinates of the point
        coords = row[0].rsplit("(", 1)[-1].rsplit(")", 1)[0].rsplit(" ", 1)
        x = float(coords[0])
        y = float(coords[1])
        point = Point(x, y)
        # check if the current point lies within the polygon or intersects it
        if point.within(polygon) or point.intersects(polygon):
            # add a "within" relationship between the point and the polygon nodes
            new_value = float(row[2]) * float(row[3])
            if "landcover" in str(row[1]):
                quads.append((row.metric, ontoEco.coveredFractionOfRegion , Literal(str(new_value), datatype=XSD.float), scenario_graph))
            else:
                quads.append((row.metric, SIO[sio_['has value']], Literal(str(new_value), datatype=XSD.float), scenario_graph))
    ds.addN(quads)

def polygonToCoords(polygon_string):
    # Extract the coordinate string from the polygon string
    match = re.search(r"\(\((.*?)\)\)", polygon_string)
    coord_string = match.group(1)

    # Split the coordinate string into pairs and convert to floats
    coords = [tuple(map(float, pair.split())) for pair in coord_string.split(",")]

    return coords[:-1]

def RDFtoDataFrame(ds, scenario_name):
    """Function that SPARQL queries the triple store and returns a Pandas DataFrame with
    the features for the SDM model"""
    sparql = """
          PREFIX myapp: <http://www.myapp.org/>
          PREFIX sio: <http://semanticscience.org/resource/SIO_>
          PREFIX ssn: <http://www.w3.org/ns/ssn/>
          PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
          PREFIX envo: <http://purl.obolibrary.org/obo/ENVO_>
          SELECT DISTINCT ?m ?l
          WHERE {
              {GRAPH myapp:ontology {
                ?m rdfs:subClassOf* ssn:Property .
                FILTER NOT EXISTS {?s rdfs:subClassOf ?m}
              }}
              UNION
              {GRAPH myapp:ecosystem {
                ?l a ?landcover .
                FILTER regex(str(?l), "No0")
              }
              GRAPH myapp:ontology {
                ?landcover rdfs:subClassOf* envo:00000043 .
                FILTER NOT EXISTS {?o rdfs:subClassOf ?landcover}
              }}
              
          }

          """
    results = ds.query(sparql)
    columns = []
    for row in results:
        for i in row:
            if i != None:
                if "No0" in i:
                    columns.append(i.rsplit("/", 1)[-1].rsplit("_", 2)[0])
                else:
                    columns.append(i.rsplit("/", 1)[-1])
    columns = sorted(columns, key=lambda s: (s[0], s))
    columns.append("x")
    columns.append("y")

    # get the coordinates of the points
    coords = getCoordsFromGraph(ds)
    # initialize the output dataframe
    df = pd.DataFrame(index=range(len(coords)), columns=columns)
    # add the coordinates to the dataframe
    for row in coords:
        match = re.match(r"POINT\((\d+\.\d+)\s+(\d+\.\d+)\)", row[1])
        x_coord = float(match.group(1))
        y_coord = float(match.group(2))
        index = int(row[0].rsplit("No", 1)[-1])
        df.loc[index, "x"] = x_coord
        df.loc[index, "y"] = y_coord
    # add the values of the metrics (features) to the dataframe
    for column in df.columns[:-2]:
        features = retrieveUpdatedFeatureFromGraph(ds, scenario_name, column)
        # update the value in the dataframe
        for row in features:
            # use the observation No to get the df index
            index = int(row[0].rsplit("No", 1)[-1])
            # update value
            if row[2] == None:
                df.loc[index, column] = float(row[1])
            else:
                df.loc[index, column] = float(row[2])
    return df
    

def getCoordsFromGraph(ds):
    sparql = """
            PREFIX geo: <http://www.opengis.net/ont/geosparql#>
            PREFIX myapp: <http://www.myapp.org/>
            SELECT DISTINCT ?point ?val
            WHERE {{
                GRAPH myapp:map {{ ?point geo:asWKT ?val .}}
            }}"""
    results = ds.query(sparql)
    return results

def retrieveUpdatedFeatureFromGraph(ds, scenario, column):
    # query the graph for each metric
    if "landcover" in column:
        sparql = """
                  PREFIX myapp: <http://www.myapp.org/>
                  PREFIX ontoEco: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoEco/>
                  SELECT ?node ?value ?value1
                  WHERE {{
                    {{
                      GRAPH myapp:ecosystem {{
                        ?node ontoEco:coveredFractionOfRegion ?value .
                      }}
                      FILTER (strstarts(str(?node), str(myapp:{col})))
                      }}
                      UNION {{
                      GRAPH myapp:{scenario} {{
                        ?node ontoEco:coveredFractionOfRegion ?value1 .
                      }}
                      FILTER (strstarts(str(?node), str(myapp:{col})))
                      }}
                  }}
                  """.format(scenario=scenario, col=column)
    else:
        sparql = """
                  PREFIX myapp: <http://www.myapp.org/>
                  PREFIX sio: <http://semanticscience.org/resource/SIO_>
                  SELECT ?node ?value ?value1
                  WHERE {{{{
                      GRAPH myapp:ecosystem {{
                        ?node sio:000300 ?value .
                      }}
                      FILTER (strstarts(str(?node), str(myapp:{col})))
                      }}
                      UNION {{
                      GRAPH myapp:{scenario} {{
                        ?node sio:000300 ?value1 .
                      }}
                      FILTER (strstarts(str(?node), str(myapp:{col})))
                      }}
                  }}
                  """.format(scenario=scenario, col=column)
    results = ds.query(sparql)
    return results

def addResultsToGraph(ds, scenario, results):
    scenario_graph = ds.graph(identifier=URIRef(MYAPP[str(scenario)]))
    quads = []
    for i in range(len(results)):
        if float(results[i][0]) > 0:
            feature_uri = MYAPP['observation_GrW_No' + str(i)]
            habitat_uri = MYAPP['occurrence_GrW_No' + str(i)]
            quads.append((habitat_uri, RO[ro_['overlaps']], feature_uri, scenario_graph))
            quads.append((habitat_uri, RDF.type, ENVO[envo_['habitat']], scenario_graph))
            quads.append((SNOMED[snomed['great reed warbler']], RO[ro_['has habitat']], habitat_uri, scenario_graph))
            quads.append((SNOMED[snomed['great reed warbler']], RO[ro_['visits']], feature_uri, scenario_graph))
            quads.append((habitat_uri, ontoEco.habitatProbability, Literal(results[i][0], datatype=XSD.float), scenario_graph))
    ds.addN(quads)


def retrieveScenarioResults(ds, scenario_name):
     
    coords = getCoordsFromGraph(ds)
    df = pd.DataFrame(index=range(len(coords)), columns=("probability", "x", "y"))
     
    for row in coords:
        match = re.match(r"POINT\((\d+\.\d+)\s+(\d+\.\d+)\)", row[1])
        x_coord = float(match.group(1))
        y_coord = float(match.group(2))
        index = int(row[0].rsplit("No", 1)[-1])
        df.loc[index, "x"] = x_coord
        df.loc[index, "y"] = y_coord
    sparql = """
                PREFIX prov: <http://www.w3.org/ns/prov#>
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX geo: <http://www.opengis.net/ont/geosparql#>
                PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX ontoEco: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoEco/>
                SELECT ?s  ?o
                WHERE {{
                GRAPH myapp:{scenario} {{
                    ?s ontoEco:habitatProbability ?o	
                    }}
                }}""".format(scenario=scenario_name)
    results = ds.query(sparql)
    for row in results:
        index = int(row[0].rsplit("No", 1)[-1])
        df.loc[index, "probability"] = float(row[1])
    return df


def compareScenarios(request):
    '''Compare scenarios view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    sparql = """
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX prov: <http://www.w3.org/ns/prov#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX ontoScenario: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/>
                SELECT DISTINCT ?scenario ?name
                WHERE 
                {{
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name ;
                            prov:wasAttributedTo myapp:user_{user} ;
                            ontoScenario:wasExecutedBy ?exec .
                        }}
                    }}
                    UNION
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name ;
                            ontoScenario:wasExecutedBy ?exec .
                        myapp:user_{user} ontoScenario:hasAccess ?scenario .
                        
                        }}
                    }}
                }}""".format(user=str(request.user.id))
    results = ds.query(sparql)
    scenarios = []
    for row in results:
        scenarios.append((row[0], row[1]))

    if request.method == 'POST':
        form = ScenarioComparisonForm(scenarios, request.POST)
        if form.is_valid():
            scenarios = form.cleaned_data['scenarios']
            img_urls = {static('img/baseScenario.png'): "Base Scenario"}
            for scenario in scenarios:
                scenario_name = scenario.split("/")[-1].rsplit("_", 1)[0]
                df = retrieveScenarioResults(ds, scenario_name)
                img_url = getResultsVisualization(df, vis_endpoint)
                img_urls[img_url] = scenario_name
            
            return render(request, "plot.html", {'scenario_img_urls': img_urls})
    else:
        form = ScenarioComparisonForm(scenarios)

    return render(request, 'select_scenario.html', {'selectform': form})


def shareScenario(request):
    '''Share scenario view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    sparql = """
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX prov: <http://www.w3.org/ns/prov#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX ontoScenario: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/>
                SELECT DISTINCT ?scenario ?name
                WHERE 
                {{
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name ;
                            prov:wasAttributedTo myapp:user_{user} .
                        }}
                    }}
                    UNION
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name .
                        myapp:user_{user} ontoScenario:hasAccess ?scenario .
                        }}
                    }}
                }}""".format(user=str(request.user.id))
    results = ds.query(sparql)
    
    options=[]
    for row in results:
        options.append((row[0], row[1]))

    if request.method == 'POST':
        form = ScenarioSharingForm(options, request.POST)
        if form.is_valid():
            scenario = request.POST['scenario']
            users = form.cleaned_data['users']
            giveAccessToScenario(ds, scenario, users)
            messages.add_message(request, messages.INFO, "Scenario shared successfully!")
            return redirect('main')
    else:
        form = ScenarioSharingForm(options)

    return render(request, 'share_scenario.html', {'shareform': form})


def giveAccessToScenario(ds, scenario, users):
    """Give access to scenario to other users"""
    scenario_graph = ds.graph(identifier=URIRef(MYAPP['scenario']))
    quads = []
    for user in users:
        quads.append((MYAPP['user_' + str(user)], ontoScenario.hasAccess, URIRef(scenario), scenario_graph))
    ds.addN(quads)


def knowledgeGraph(request):
    '''Knowledge Graph view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    
    cyto.load_extra_layouts()

    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))

    ds.bind("ecso", ECSO, override=True)
    ds.bind("ro", RO, override=True)
    ds.bind("envo", ENVO, override=True)
    ds.bind("sio", SIO, override=True)
    ds.bind("sct", SNOMED, override=True)
    ds.bind("ssn", SSN, override=True)
    ds.bind("geo", GEOSPARQL, override=True)
    ds.bind("myapp", MYAPP, override=True)
    ds.bind("gml", GML, override=True)
    ds.bind("ncit", NCIT, override=True)
    ds.bind("bfo", BFO, override=True)
    ds.bind("prov", PROV, override=True)
    ds.bind("ontoEco", ontoEco, override=True)
    ds.bind("ontoGeo", ontoGeo, override=True)
    ds.bind("ontoScenario", ontoScenario, override=True)

    elements = []

    sparql = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?domain ?property ?range ?l1 ?l2 ?l3
                WHERE {{
                {{
                    {{
                        GRAPH myapp:ontology {{
                            ?domain a owl:Class .
                            ?domain rdfs:subClassOf* ?res .
                            ?res a owl:Restriction ;
                                owl:onProperty ?property ;
                                ?p2 ?range .
                            ?range a owl:Class .
                        }}
                    }}
                    UNION
                    {{
                        GRAPH myapp:ontology {{
                            ?domain a owl:Class .
                            ?domain rdfs:subClassOf* ?res .
                            ?res a owl:Restriction ;
                                owl:onProperty ?property ;
                                owl:someValuesFrom ?range .
                        }}
                    }}
                    OPTIONAL {{ ?domain rdfs:label ?l1 . }}
                    OPTIONAL {{ ?property rdfs:label ?l2 . }}
                    OPTIONAL {{ ?range rdfs:label ?l3 . }}   
                }}
            }}"""
    results =ds.query(sparql)
    for row in results:
        if row[1] != None:
            data = {'id': row[0].n3(ds.namespace_manager), 'label': row[3]}
            elements.append({'data': data})
            data = {'id': row[2].n3(ds.namespace_manager), 'label': row[5]}
            elements.append({'data': data})
            data = {'source': row[0].n3(ds.namespace_manager), 'target': row[2].n3(ds.namespace_manager), 'label': row[4]}
            elements.append({'data': data})
    sparql = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?domain ?range ?l1 ?l2
                WHERE {{
                {{
                    
                        GRAPH myapp:ontology {{
                            ?domain rdfs:subClassOf ?range .
                            ?domain a owl:Class .
                            ?range a owl:Class .
                        }}
                    
                    OPTIONAL {{ ?domain rdfs:label ?l1 . }}
                    OPTIONAL {{ ?range rdfs:label ?l2 . }}  
                }}
                FILTER (!isBlank(?range))
                FILTER (!isBlank(?domain))
            }}"""
    results =ds.query(sparql)
    for row in results:
        data = {'id': row[0].n3(ds.namespace_manager), 'label': row[2]}
        elements.append({'data': data})
        data = {'id': row[1].n3(ds.namespace_manager), 'label': row[3]}
        elements.append({'data': data})
        data = {'source': row[0].n3(ds.namespace_manager), 'target': row[1].n3(ds.namespace_manager), 'label': 'rdfs:subClassOf'}
        elements.append({'data': data})


    cytoscape_style = [
        {
            'selector': 'node',
            'style': {
                'background-color': '#D3D3D3',
                'label': 'data(label)',
                'shape': 'roundrectangle',
                'width': 'label',
                'height': 'label',
                'padding': '10px',
                'font-size': '15px',
                'text-valign': 'center',
                'text-halign': 'center',
                'text-outline-color': '#967bb6',
                'text-outline-width': '1px'
            }
        },
        {
            'selector': 'edge',
            'style': {
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#967bb6',
                'line-color': '#967bb6',
                'width': 2,
                'arrow-scale': 1,
                'opacity': 1,
                'label': 'data(label)',
                'font-size': '10px',
                'text-outline-color': '#D3D3D3',
                'text-outline-width': '1px'
            }
        },
        {
            'selector': ':selected',
            'style': {
                'background-color': '#517593',
                'line-color': '#517593',
                'target-arrow-color': '#517593',
                'source-arrow-color': '#517593',
                'opacity': 1
            }
        },
        {
            'selector': '.highlighted',
            'style': {
                'background-color': '#00FF00',
                'line-color': '#00FF00',
                'target-arrow-color': '#00FF00',
                'source-arrow-color': '#00FF00',
                'opacity': 1
            }
        },
        {
            'selector': '.hidden',
            'style': {
                'display': 'none'
            }
        }
    ]

    # Build App
    app = DjangoDash("KnowledgeGraph")
    app.layout = html.Div([html.Div([
            # Node ID input
            html.Label('Search Class: ', style={'color': '#ffffff'}),
            html.Div([
                html.Div([
                    dcc.Input(id='node_id', type='text', value='')
                ], className='col-md-8'),
            ], className='row'),
        ], style= {'display': 'flex', 'align-items': 'center', 'justify-content': 'center', 'padding-bottom': '10px'}),
        html.Div([
        cyto.Cytoscape(
            id='cytoscape-graph',
            elements=elements,
            layout={
            'name': 'klay', 
            }, 
            style={'width': '100%', 'height': 'calc(100vh - 100px)'},
            stylesheet=cytoscape_style
        )
    ]
    )
    ])

    # Callback to update the graph with the selected node and its neighbors
    @app.callback(
        Output('cytoscape-graph', 'elements'),
        Input('node_id', 'value')
    )
    def update_graph(node_id):
        filter_clause = f'FILTER (regex(str(?domain), "{node_id}$", "i") || regex(str(?property), "{node_id}", "i") || regex(str(?range), "{node_id}$", "i"))'
        if not node_id:
            # If no node ID is entered, return the full graph data
            return elements
        new_elements = []
        sparql = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?domain ?property ?range ?l1 ?l2 ?l3
                WHERE {{
                {{
                    {{
                        GRAPH myapp:ontology {{
                            ?domain a owl:Class .
                            ?domain rdfs:subClassOf* ?res .
                            ?res a owl:Restriction ;
                                owl:onProperty ?property ;
                                ?p2 ?range .
                            ?range a owl:Class .
                        }}
                    }}
                    UNION
                    {{
                        GRAPH myapp:ontology {{
                            ?domain a owl:Class .
                            ?domain rdfs:subClassOf* ?res .
                            ?res a owl:Restriction ;
                                owl:onProperty ?property ;
                                owl:someValuesFrom ?range .
                        }}
                    }}
                    OPTIONAL {{ ?domain rdfs:label ?l1 . }}
                    OPTIONAL {{ ?property rdfs:label ?l2 . }}
                    OPTIONAL {{ ?range rdfs:label ?l3 . }}   
                }}
                {filter}
            }}""".format(filter=filter_clause)
        results =ds.query(sparql)
        for row in results:
            if row[1] != None:
                data = {'id': row[0].n3(ds.namespace_manager), 'label': row[3]}
                new_elements.append({'data': data})
                data = {'id': row[2].n3(ds.namespace_manager), 'label': row[5]}
                new_elements.append({'data': data})
                data = {'source': row[0].n3(ds.namespace_manager), 'target': row[2].n3(ds.namespace_manager), 'label': row[4]}
                new_elements.append({'data': data})
        sparql = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?domain ?range ?l1 ?l2
                WHERE {{
                {{
                    
                        GRAPH myapp:ontology {{
                            ?domain rdfs:subClassOf ?range .
                            ?domain a owl:Class .
                            ?range a owl:Class .
                        }}
                    
                    OPTIONAL {{ ?domain rdfs:label ?l1 . }}
                    OPTIONAL {{ ?range rdfs:label ?l2 . }}  
                }}
                FILTER (!isBlank(?range))
                FILTER (!isBlank(?domain))
                {filter}
            }}""".format(filter=filter_clause)
        results =ds.query(sparql)
        for row in results:
            data = {'id': row[0].n3(ds.namespace_manager), 'label': row[2]}
            new_elements.append({'data': data})
            data = {'id': row[1].n3(ds.namespace_manager), 'label': row[3]}
            new_elements.append({'data': data})
            data = {'source': row[0].n3(ds.namespace_manager), 'target': row[1].n3(ds.namespace_manager), 'label': 'rdfs:subClassOf'}
            new_elements.append({'data': data})
            
        if len(new_elements) > 0:
            return new_elements
        else:
            return elements
    """fuseki_endpoint = os.getenv("SPARQL_ENDPOINT", "http://localhost:3030/")
    context = {
        "sparql_endpoint": fuseki_endpoint
    }"""
    return render(request, 'ontology.html')

def deleteScenario(request):
    '''Delete scenario view'''
    # Check if authenticated
    if not request.user.is_authenticated:
        return HttpResponse("Unauthenticated")
    
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    sparql = """
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX prov: <http://www.w3.org/ns/prov#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX ontoScenario: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/>
                SELECT DISTINCT ?scenario ?name
                WHERE 
                {{
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name ;
                            prov:wasAttributedTo myapp:user_{user} .
                        }}
                    }}
                    UNION
                    {{
                        GRAPH myapp:scenario 
                        {{
                        ?scenario rdfs:label ?name .
                        myapp:user_{user} ontoScenario:hasAccess ?scenario .
                        }}
                    }}
                }}""".format(user=str(request.user.id))
    results = ds.query(sparql)
    
    options=[]
    for row in results:
        options.append((row[0], row[1]))

    if request.method == 'POST':
        form = ScenarioSelectionForm(options, request.POST)
        if form.is_valid():
            scenario = request.POST['scenario']
            scenario = scenario.rsplit('_', 1)[0]
            ds.remove_graph(ds.get_context(URIRef(scenario)))
            graph = ds.get_context(MYAPP.scenario)
            for s, p, o in graph.triples((None, None, None)):
                if scenario.split('/')[-1] in str(s):
                    graph.remove((s, p, o))
            messages.add_message(request, messages.INFO, "Scenario deleted successfully!")
            return redirect('main')
    else:
        form = ScenarioSelectionForm(options)

    return render(request, 'delete_scenario.html', {'deleteform': form})