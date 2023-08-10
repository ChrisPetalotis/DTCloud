import subprocess
import json
import os
import mappingAgents as ma
import queryAgents as qa
from rdflib import Dataset, Namespace, URIRef, Literal, RDF, RDFS, XSD
import glob
import hcl2


endpoint = "http://localhost:3030/ds/"

DOCKER = Namespace("https://w3.org/ns/bde/docker#")
MYAPP = Namespace("http://www.myapp.org/")
ontoContainer = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/")
ontoDeploy = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoDeploy/")


def ingestAttributeToOntology(output_data, resourceType, resourceName, attributes, infraClasses, infraProps, infraGraph):
    resource = resourceType+'_'+resourceName
    for attr, value in attributes.items():
        if type(value) in [str, int, float, bool]:
            handleHostRelationship(output_data, infraGraph, resourceType, resource, attr, value)
            prop = ma.mapInputToProperty(attr, infraProps, False, True)
            if attr == 'type':
                cls = ma.mapColumnToClass(value, infraClasses, False, True)
                quads.append((MYAPP[resource], RDF.type, URIRef(cls), infraGraph))
                if cls.endswith('Forward'):
                    handleStringAttribute(infraGraph, resource, ontoDeploy.targetGroup, attributes['target_group_arn'])
            elif prop != None:
                if 'key' not in resourceType and attr == 'key_name':
                    prop = ontoDeploy.key
                handleStringAttribute(infraGraph, resource, prop, str(value))
                if resourceType == 'aws_appautoscaling_policy' and attr == 'service_namespace':
                    prop = ontoDeploy.target
                    handleStringAttribute(infraGraph, resource, prop, str(value))
        elif type(value) == list:
            if type(value[0]) in [str, int, float, bool]:
                prop = ma.mapInputToProperty(attr, infraProps, False, True)
                for v in value:
                    if prop != None:
                        handleStringAttribute(infraGraph, resource, prop, str(v))
            elif type(value[0]) == dict:
                i = 0
                for v in value:
                    i += 1
                    cls = ma.mapColumnToClass(attr, infraClasses, False, True)
                    if cls.endswith('PathPattern'):
                        quads.append((MYAPP[resource], RDF.type, URIRef(cls), infraGraph))
                        quads.append((MYAPP[resource], ontoDeploy.hasValue, Literal(v['values'][0], datatype=XSD.string), infraGraph))
                    elif cls.endswith('TargetTrackingPolicy'):
                        quads.append((MYAPP[resource], RDF.type, URIRef(cls), infraGraph))
                        newProps = qa.getOntologyProperties(endpoint, [cls+"$"], 'domain')
                        ingestAttributeToOntology(output_data, resourceType, resourceName, v, infraClasses, newProps, infraGraph)
                    else:
                        if cls.endswith('LoadBalancer') and resourceType == 'aws_ecs_service':
                            cls = ontoDeploy.ECSServiceLBConfig
                        quads.append((MYAPP[resourceName+"."+attr+'_'+str(i)], RDF.type, URIRef(cls), infraGraph))
                        prop = ma.mapInputToProperty(attr, infraProps, False, True)
                        if prop != None:
                            quads.append((MYAPP[resource], URIRef(prop), MYAPP[resourceName+"."+attr+'_'+str(i)], infraGraph))
                            newProps = qa.getOntologyProperties(endpoint, [cls+"$"], 'domain')
                            ingestAttributeToOntology(output_data, resourceName, attr+'_'+str(i), v, infraClasses, newProps, infraGraph)
        elif type(value) == dict:
            cls = ma.mapColumnToClass(attr, infraClasses, False, True)
            if cls.endswith('Variable'):
                for varName, varValue in value.items():
                    quads.append((MYAPP[resource], ontoDeploy.hasEnvVar, MYAPP[resourceName+"."+attr+'_var_'+varName], infraGraph))
                    quads.append((MYAPP[resourceName+"."+attr+'_var_'+varName], RDF.type, ontoDeploy.Variable, infraGraph))
                    quads.append((MYAPP[resourceName+"."+attr+'_var_'+varName], ontoDeploy.hasName, Literal(varName, datatype=XSD.string), infraGraph))
                    quads.append((MYAPP[resourceName+"."+attr+'_var_'+varName], ontoDeploy.hasValue, Literal(varValue, datatype=XSD.string), infraGraph))
            else:
                quads.append((MYAPP[resourceName+"."+attr], RDF.type, URIRef(cls), infraGraph))
                prop = ma.mapInputToProperty(attr, infraProps, False, True)
                if prop != None:
                    quads.append((MYAPP[resource], URIRef(prop), MYAPP[resourceName+"."+attr], infraGraph))
                    newProps = qa.getOntologyProperties(endpoint, [cls+"$"], 'domain')
                    ingestAttributeToOntology(output_data, resourceName, attr, value, infraClasses, newProps, infraGraph)

def handleStringAttribute(infraGraph, resource, prop, value):
    quads.append((MYAPP[resource], URIRef(prop), Literal(value, datatype=XSD.string), infraGraph))
    if 'aws_' in value:
        if '$' in value:
            value = value.split('{')[-1].split('}')[0]
        value = value.split('.')
        object = value[0]+'_'+value[1]
        quads.append((MYAPP[resource], URIRef(prop), MYAPP[object], infraGraph))
    if 'template_file' in value:
        if '$' in value:
            value = value.split('{')[-1].split('}')[0]
        value = value.split('.')
        object = value[1]+'_'+value[2]
        quads.append((MYAPP[resource], URIRef(prop), MYAPP[object], infraGraph))
    if 'var.' in value:
        if '$' in value:
            value = value.split('{')[-1].split('}')[0]
        var = 'variable_' + value.split('.')[1]
        quads.append((MYAPP[resource], ontoDeploy.requiresVariable, MYAPP[var], infraGraph))
    
def handleHostRelationship(output_data, infraGraph, resourceType, resource, attr, value):
    if 'ecs' in resourceType:
        if 'service' in resourceType:
            if attr == 'cluster':
                handleStringAttribute(infraGraph, resource, ontoDeploy.hostedOn, value)
            elif attr == 'task_definition':
                handleStringAttribute(infraGraph, resource, ontoDeploy.hosts, value)
        if 'task_definition' in resourceType:
            if attr == 'container_definitions':
                for r in output_data['data']:
                    try:
                        if value.split(".")[2] in r['template_file'].keys():
                            for key, val in r['template_file'][value.split(".")[2]]['vars'].items():
                                cls = ma.mapColumnToClass(key, dockerClasses, False, True)
                                instances = qa.getInstancesOfClass(endpoint, cls)
                                prop = ma.mapInputToProperty(key, instances, False, True)
                                for instance in instances:
                                    if str(instance[1]) == str(prop) and str(instance[2]) == str(val):
                                        quads.append((MYAPP[resource], ontoDeploy.hosts, URIRef(instance[0]), infraGraph))
                                        quads.append((URIRef(instance[0]), ontoDeploy.hostedOn, MYAPP[resource], infraGraph))
                    except:
                        pass


quads = []

def ingestInfra(endpoint, infra):
    # Parse the JSON output into a Python dictionary
    folder_path = f"./terraform/{infra}"
    # Search for files with .tf extension in the folder
    file_pattern = f"{folder_path}/*.tf"
    tf_files = glob.glob(file_pattern)

    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))
    ds.remove_graph(ds.get_context(URIRef("http://www.myapp.org/infrastructure")))
    infraGraph = ds.graph(URIRef("http://www.myapp.org/infrastructure"))
    # Iterate over the .tf files and read their contents
    for file_path in tf_files:
        with open(file_path, 'r') as f:
            output_data = hcl2.load(f)

        if 'resource' in output_data.keys():

            for resource in output_data['resource']:
                for resourceType, instances in resource.items():
                    cls = ma.mapColumnToClass(resourceType.split("_", 1)[-1], infraClasses, False, True)
                    for name, attrs in instances.items():
                        quads.append((MYAPP[resourceType+'_'+name], RDF.type, URIRef(cls), infraGraph))
                        if str(cls) == str(ontoDeploy.Subnet):
                            if 'pubic' in name:
                                quads.append((MYAPP[resourceType+'_'+name], RDF.type, ontoDeploy.PublicSubnet, infraGraph))
                            elif 'private' in name:
                                quads.append((MYAPP[resourceType+'_'+name], RDF.type, ontoDeploy.PrivateSubnet, infraGraph))
                        infraProps = qa.getOntologyProperties(endpoint, [cls+"$"], 'domain')
                        ingestAttributeToOntology(output_data, resourceType, name, attrs, infraClasses, infraProps, infraGraph)

        if 'data' in output_data.keys():
            for data in output_data['data']:
                for dataType, instances in data.items():
                    cls = ma.mapColumnToClass(dataType, infraClasses, False, True)
                    if cls != None:
                        for name, attrs in instances.items():
                            quads.append((MYAPP[dataType+'_'+name], RDF.type, URIRef(cls), infraGraph))
                            infraProps = qa.getOntologyProperties(endpoint, [cls+"$"], 'domain')
                            ingestAttributeToOntology(output_data, dataType, name, attrs, infraClasses, infraProps, infraGraph)

        if 'provider' in output_data.keys():
            resourceType = 'provider'
            for provider in output_data['provider']:
                for providerName, providerAttrs in provider.items():
                    resource = resourceType + '_' + providerName
                    quads.append((MYAPP[resource], RDF.type, ontoDeploy.CloudProvider, infraGraph))
                    infraProps = qa.getOntologyProperties(endpoint, [ontoDeploy.CloudProvider], 'domain')
                    for attr, value in providerAttrs.items():
                        prop = ma.mapInputToProperty(attr, infraProps, False, True)
                        if prop != None:
                            handleStringAttribute(infraGraph, resource, prop, str(value))

        if 'variable' in output_data.keys():
            resourceType = 'variable'
            for variable in output_data['variable']:
                for varName, varAttrs in variable.items():
                    resource = resourceType + '_' + varName
                    quads.append((MYAPP[resource], RDF.type, ontoDeploy.Variable, infraGraph))
                    infraProps = qa.getOntologyProperties(endpoint, [ontoDeploy.Variable], 'domain')
                    for attr, value in varAttrs.items():
                        prop = ma.mapInputToProperty(attr, infraProps, False, True)
                        if prop != None:
                            handleStringAttribute(infraGraph, resource, prop, str(value))

        if 'output' in output_data.keys():
            resourceType = 'output'
            for variable in output_data['output']:
                for varName, varAttrs in variable.items():
                    resource = resourceType + '_' + varName
                    quads.append((MYAPP[resource], RDF.type, ontoDeploy.Output, infraGraph))
                    infraProps = qa.getOntologyProperties(endpoint, [ontoDeploy.Variable], 'domain')
                    for attr, value in varAttrs.items():
                        prop = ma.mapInputToProperty(attr, infraProps, False, True)
                        if prop != None:
                            handleStringAttribute(infraGraph, resource, prop, str(value))
                        
    ds.addN(quads)

#import time 

#start = time.time()
dockerClasses = qa.getOntologyClasses(endpoint, ['docker#'])
infraClasses = qa.getOntologyClasses(endpoint, ['deploy'], True)
#mid = time.time()
#ingestInfra(endpoint, 'db')
#ingestInfra(endpoint, 'scenariodt_infra')
#end = time.time()


#print('Ontology classes retrieval time: ' + str(mid - start) + ' seconds')
#print('Infra ingestion time: ' + str(end - mid) + ' seconds')
#print('Total time: ' + str(end - start) + ' seconds')
                    
