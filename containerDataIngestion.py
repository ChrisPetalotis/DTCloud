import docker
from rdflib import Dataset, Literal, Namespace, RDF, XSD
from typing import TypeVar
import queryAgents as qa
import mappingAgents as ma

SPARQLEndpoint = TypeVar('SPARQLEndpoint', str, str)
filePath = TypeVar('filePath', str, str)
endpoint = "http://localhost:3030/ds/"
# Define the Docker vocabulary namespace
DOCKER = Namespace("https://w3.org/ns/bde/docker#")
MYAPP = Namespace("http://www.myapp.org/")
ontoContainer = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/")
ontoFlow = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoFlow/")
ontoDeploy = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoDeploy/")



def addContainerToKnowledgeGraph(ds, graph, client, container_name, services):
    
    container_info = client.inspect_container(container_name)
    container_id = container_info['Id'][:12]
    entities = []
    dockerClasses = qa.getOntologyClasses(endpoint, ['docker#'])
    for c in dockerClasses:
        entity = c[0].split('#')[-1]
        entities.append(entity)
    
    results = ingestContainerInspectData(graph, container_info, container_id, entities)

    ports = container_info['NetworkSettings']['Ports']
    for key, val in ports.items():
        container_port = key.split('/')[0]
        if val != None:
            host_port = val[0]['HostPort']
            results.append((MYAPP['docker_' + container_id + '_containerPort_' + container_port], RDF.type, ontoContainer.ContainerPort, graph))
            results.append((MYAPP['docker_' + container_id + '_hostPort_' + host_port], RDF.type, ontoContainer.HostPort, graph))
            results.append((MYAPP['docker_' + container_id + '_networksettings'], ontoContainer.exposesPort, MYAPP['docker_' + container_id + '_containerPort_' + container_port], graph))
            results.append((MYAPP['docker_' + container_id + '_containerPort_' + container_port], ontoContainer.hasValue, Literal(container_port, datatype=XSD.string), graph))
            results.append((MYAPP['docker_' + container_id + '_hostPort_' + host_port], ontoContainer.hasValue, Literal(host_port, datatype=XSD.string), graph))
            results.append((MYAPP['docker_' + container_id + '_containerPort_' + container_port], ontoContainer.mapsTo, MYAPP['docker_' + container_id + '_hostPort_' + host_port], graph))
    network = container_info['HostConfig']['NetworkMode']
    results.append((MYAPP['docker_' + container_id + '_networks'], ontoContainer.hasName, Literal(network, datatype=XSD.string), graph))

    
    service = ma.mapContainerToService(container_name, services)
    if service != None:
        results.append((MYAPP['docker_' + container_id + '_container'], ontoDeploy.hosts, service, graph))
        results.append((service, ontoContainer.hosted_in, MYAPP['docker_' + container_id + '_container'], ds.graph(MYAPP['service'])))

    return results

def addImageToKnowledgeGraph(graph, client, image):
    image_info = client.inspect_image(image)
    image_id = image_info['Id']
    image_id_short = image_info['Id'].split(':')[-1][:12]
    results = ingestContainerInspectData(graph, image_info, image_id_short, ['Image'], 'Image')
    return results, image_id

def ingestContainerInspectData(graph, dictionary, container_id, entities, dic_name='Container'):
    results = []
    strictMapping = True
    if dic_name == 'Image':
        strictMapping = False
    entity_uri = MYAPP['docker_' + container_id + '_' + dic_name.lower()]
    if dic_name in entities:
        entity_class = ma.mapColumnToClass(dic_name, dockerClasses, strictMapping)
        results.append((entity_uri, RDF.type, entity_class, graph))
    for key, value in dictionary.items():
        if dic_name == 'Config' and 'image' in key.lower(): # skip the image data within Config
            continue
        key_uri = MYAPP['docker_' + container_id + '_' + key.lower()]
        if type(value) in [str, int, float] and value != "": # if it is a string, it is a data property
            if key == 'Name':
                value = value.replace('/', '')
            p = ma.mapInputToProperty(key, props, strictMapping)
            if p != None and dic_name in entities:
                results.append((entity_uri, p, Literal(str(value), datatype=XSD.string), graph))
        elif type(value) == list: # if it is a list, it could be a class
            c = ma.mapColumnToClass(key, dockerClasses, strictMapping)
            if c != None and dic_name in entities:
                p = ma.findPropertyBasedOnDomainRangePair(props, dic_name, key)
                if p != None:
                    results.append((key_uri, RDF.type, c, graph))
                    results.append((entity_uri, p, key_uri, graph))
            if key == 'Cmd': # if it is a command, join all command elements into a single string
                value = ' '.join(value)
                p = ma.mapInputToProperty(key, props, strictMapping)
                results.append((entity_uri, p, Literal(value, datatype=XSD.string), graph))
            elif key == 'Entrypoint' and len(value) > 1: # if it is an entrypoint, join all entrypoint elements into a single string
                value = '", "'.join(value)
                value = '["' + value + '"]'
                p = ma.mapInputToProperty(key, props, strictMapping)
                results.append((entity_uri, p, Literal(value, datatype=XSD.string), graph))
            else: # if it is not a command, check each element
                for v in value:
                    if type(v) in [str, int, float]: 
                        if key == 'Env': # if the key was Env, the elements are evnironment variables
                            var_uri = MYAPP['docker_' + container_id + "_envVar_" + v.split('=')[0]]
                            results.append((var_uri, RDF.type, ontoContainer.EnvVar, graph))
                            results.append((key_uri, ontoContainer.hasEnvVar, var_uri, graph))
                            results.append((var_uri, ontoContainer.hasName, Literal(v.split('=')[0], datatype=XSD.string), graph))
                            results.append((var_uri, ontoContainer.hasValue, Literal(v.split('=')[1]), graph))
                        else: # if it is not an environment variable, it is a data property
                            p = ma.mapInputToProperty(key, props, strictMapping)
                            if p != None:
                                results.append((entity_uri, p, Literal(str(v), datatype=XSD.string), graph))
                    elif type(v) == dict: # if it is a dictionary, repeat the process recursively
                        subsubresults = ingestContainerInspectData(graph, v, container_id, entities, key)
                        results.extend(subsubresults)       
        elif type(value) == dict and dic_name != 'Image': # if it is a dictionary, check it's a class, then repeat the process recursively
            c = ma.mapColumnToClass(key, dockerClasses, strictMapping)
            if c != None and dic_name in entities:
                p = ma.findPropertyBasedOnDomainRangePair(props, dic_name, key)
                if p != None:
                    results.append((key_uri, RDF.type, c, graph))
                    results.append((entity_uri, p, key_uri, graph))
            subresults = ingestContainerInspectData(graph, value, container_id, entities, key)
            results.extend(subresults)
    return results

filters = ['docker', 'container']
props = qa.getOntologyProperties(endpoint, filters)
dockerClasses = qa.getOntologyClasses(endpoint, ['docker#'])

def ingestContainers(endpoint):
    endpoint_query = endpoint + 'sparql'
    endpoint_update = endpoint + 'update'
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    ds.bind('myapp', MYAPP, override=True)
    ds.bind('ontoContainer', ontoContainer)
    ds.bind('docker', DOCKER)
    ds.remove_graph(ds.get_context(MYAPP['container']))
    graph = ds.graph(MYAPP['container'])

    
    
    # get all existing containers
    client = docker.from_env()
    services = qa.getDTService(endpoint)

    for c in client.containers(all=True):
        container_name = c['Names'][0].split('/')[1]
        results = addContainerToKnowledgeGraph(ds, graph, client, container_name, services)
        ds.addN(results)

    for i in client.images():
        image_name = i['RepoTags'][0]
        imageResults, image_id = addImageToKnowledgeGraph(graph, client, image_name)
        ds.addN(imageResults)
        for container, hasImage, imgID in graph.triples((None, DOCKER.image, Literal(image_id, datatype=XSD.string))):
            graph.remove((container, hasImage, imgID))
            for image, hasID, id in graph.triples((None, DOCKER.id, Literal(image_id, datatype=XSD.string))):
                ds.add((container, hasImage, image, graph))



#print(graph.serialize(format='turtle'))



