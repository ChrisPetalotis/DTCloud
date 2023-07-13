from rdflib import Namespace
from rdflib.plugins.sparql.processor import SPARQLResult
from typing import TypeVar

SPARQLEndpoint = TypeVar('SPARQLEndpoint', str, str)
filePath = TypeVar('filePath', str, str)

# Define the Docker vocabulary namespace
DOCKER = Namespace("https://w3.org/ns/bde/docker#")
MYAPP = Namespace("http://www.myapp.org/")
ontoContainer = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/")
ontoFlow = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoFlow/")
endpoint = "http://localhost:3030/ds/"

def getOntologyClasses(endpoint :SPARQLEndpoint, filters :list = [], parents :bool = False) -> SPARQLResult:
    
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))
    if parents:
        parents_filter = ""
    else:
        parents_filter = "FILTER NOT EXISTS {{?subclass rdfs:subClassOf ?class .}}"
    filter_clause = " || ".join([f'regex(str(?class), "{filter}", "i")' for filter in filters])
    filter_clause = f'FILTER ({filter_clause})' if filter_clause else ''

    sparql = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?class ?label ?description
    WHERE {{
      GRAPH ?g {{
      ?class a owl:Class.
      {parents_filter}
      OPTIONAL {{ ?class rdfs:label ?label}}
      OPTIONAL {{ ?class rdfs:comment ?description}}
    }}
    {filter}
    }}""".format(filter=filter_clause, parents_filter=parents_filter)
    
    results=ds.query(sparql)
    return results

def getOntologyProperties(endpoint :SPARQLEndpoint, filters :list = [], filterType :str = 'property') -> SPARQLResult:
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))

    filter_clause = " || ".join([f'regex(str(?{filterType}), "{filter}", "i")' for filter in filters])
    filter_clause = f'FILTER ({filter_clause})' if filter_clause else ''
    
    sparql = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?domain ?property ?range ?l1 ?l2 ?l3
                WHERE {{
                {{
                    ?range rdfs:subClassOf* ?parent2 .
                    ?property rdfs:range ?parent2 .
                    OPTIONAL {{ ?property rdfs:domain ?domain .
                        OPTIONAL {{ ?domain rdfs:label ?l1 . }}
                    }}
                    OPTIONAL {{ ?property rdfs:label ?l2 . }}
                    OPTIONAL {{ ?range rdfs:label ?l3 . }} 
                }}
                UNION
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
    results = ds.query(sparql)
    return results

def getDTService(endpoint :SPARQLEndpoint, filters :list = []) -> SPARQLResult:
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))

    filter_clause = " || ".join([f'regex(str(?instance), "{filter}", "i")' for filter in filters])
    filter_clause = f'FILTER ({filter_clause})' if filter_clause else ''

    sparql = """PREFIX myapp: <http://www.myapp.org/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX ontoFlow: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoFlow/>
                SELECT DISTINCT ?instance ?name ?desc ?language
                WHERE {{
                    ?instance a/rdfs:subClassOf* ontoFlow:Service .
                    OPTIONAL {{ ?instance ontoFlow:hasName ?name . }}
                    OPTIONAL {{ ?instance ontoFlow:hasDescription ?desc . }}
                    OPTIONAL {{ ?instance ontoFlow:hasLanguage ?language . }}
                    {filter}
                }}""".format(filter=filter_clause)
    results = ds.query(sparql)
    return results
                    

def getContainerEnvVar(endpoint :SPARQLEndpoint, filters :list = []) -> SPARQLResult:
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))

    filter_clause = " || ".join([f'regex(str(?container), "{filter}", "i")' for filter in filters])
    filter_clause = f'FILTER ({filter_clause})' if filter_clause else ''

    sparql = """PREFIX myapp: <http://www.myapp.org/>
                PREFIX ontoContainer: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/>
                PREFIX docker: <https://w3.org/ns/bde/docker#>
                SELECT DISTINCT ?name ?value
                WHERE {{
                    GRAPH myapp:container {{
                        ?c a docker:Container ;
                            docker:name ?container ;
                            docker:config/docker:env/ontoContainer:hasEnvVar ?var .
                        ?var ontoContainer:hasName ?name ;
                            ontoContainer:hasValue ?value .
                    }}
                    {filter}
                    }}""".format(filter=filter_clause)
    results = ds.query(sparql)
    return results

def getContainerCmd(endpoint :SPARQLEndpoint, filters :list = []) -> SPARQLResult:
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))

    filter_clause = " || ".join([f'regex(str(?container), "{filter}", "i")' for filter in filters])
    filter_clause = f'FILTER ({filter_clause})' if filter_clause else ''

    sparql = """PREFIX myapp: <http://www.myapp.org/>
                PREFIX ontoContainer: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/>
                PREFIX docker: <https://w3.org/ns/bde/docker#>
                SELECT DISTINCT ?cmd
                WHERE {{
                    GRAPH myapp:container {{
                        ?c a docker:Container ;
                            docker:name ?container ;
                            docker:config/docker:cmd ?cmd .
                    }}
                    {filter}
                    }}""".format(filter=filter_clause)
    results = ds.query(sparql)
    return results

def getContainerImage(endpoint :SPARQLEndpoint, filters :list = []) -> SPARQLResult:
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))

    filter_clause = " || ".join([f'regex(str(?container), "{filter}", "i")' for filter in filters])
    filter_clause = f'FILTER ({filter_clause})' if filter_clause else ''

    sparql = """PREFIX myapp: <http://www.myapp.org/>
                PREFIX ontoContainer: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/>
                PREFIX docker: <https://w3.org/ns/bde/docker#>
                SELECT DISTINCT ?image
                WHERE {{
                    GRAPH myapp:container {{
                        ?c a docker:Container ;
                            docker:name ?container ;
                            docker:image/docker:tags ?image .
                    }}
                    {filter}
                    }}""".format(filter=filter_clause)
    results = ds.query(sparql)
    return results

def getContainerPorts(endpoint :SPARQLEndpoint, filters :list = []) -> SPARQLResult:
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))

    filter_clause = " || ".join([f'regex(str(?container), "{filter}", "i")' for filter in filters])
    filter_clause = f'FILTER ({filter_clause})' if filter_clause else ''

    sparql = """PREFIX myapp: <http://www.myapp.org/>
                PREFIX ontoContainer: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/>
                PREFIX docker: <https://w3.org/ns/bde/docker#>
                SELECT DISTINCT ?containerPortValue ?hostPortValue
                WHERE {{
                    GRAPH myapp:container {{
                        ?c a docker:Container ;
                            docker:name ?container ;
                            docker:networkSettings/ontoContainer:exposesPort ?containerPort .
                        ?containerPort ontoContainer:mapsTo/ontoContainer:hasValue ?hostPortValue ;
                            ontoContainer:hasValue ?containerPortValue .
                    }}
                    {filter}
                    }}""".format(filter=filter_clause)
    results = ds.query(sparql)
    return results

def getContainers(endpoint :SPARQLEndpoint, filters :list = []) -> SPARQLResult:
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))

    filter_clause = " || ".join([f'regex(str(?container), "{filter}", "i")' for filter in filters])
    filter_clause = f'FILTER ({filter_clause})' if filter_clause else ''

    sparql = """PREFIX myapp: <http://www.myapp.org/>
                PREFIX ontoContainer: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoContainer/>
                PREFIX docker: <https://w3.org/ns/bde/docker#>
                SELECT DISTINCT ?c ?container
                WHERE {{
                    GRAPH myapp:container {{
                        ?c a docker:Container ;
                            docker:name ?container .
                    }}
                    {filter}
                    }}""".format(filter=filter_clause)
    results = ds.query(sparql)
    return results

def getInstancesOfClass(endpoint :SPARQLEndpoint, classURI :str) -> SPARQLResult:
    from rdflib import Dataset
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))
    sparql = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX myapp: <http://www.myapp.org/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT ?instance ?property ?value ?l1 ?l2 ?l3
                WHERE {{
                        ?instance a <{classURI}> .
                        ?instance ?property ?value .
                        OPTIONAL {{ ?instance rdfs:label ?l1 }}
                        OPTIONAL {{ ?property rdfs:label ?l2 }}
                        OPTIONAL {{ ?value rdfs:label ?l3 }}
                    }}
            """.format(classURI=classURI)
    results = ds.query(sparql)
    return results

