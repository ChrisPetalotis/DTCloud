from rdflib import Dataset, Namespace, URIRef, Literal, XSD, RDF, RDFS
from rdflib.plugins.sparql.processor import SPARQLResult
from shapely.geometry import Point, Polygon
import pandas as pd
from typing import TypeVar
import queryAgents as qa
import mappingAgents as ma

SPARQLEndpoint = TypeVar('SPARQLEndpoint', str, str)
filePath = TypeVar('filePath', str, str)

# Define namespaces
GML = Namespace("http://www.opengis.net/gml/3.2/")
MYAPP = Namespace("http://www.myapp.org/")
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

ontoGeo = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoGeo/")
ontoEco = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoEco/")
ontoScenario = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoScenario/")

domain_ontologies = ['ENVO_', 'ECSO_', 'RO_', 'SIO_', 'ssn', 'snomed', 'NCIT_', 'BFO_', 'ontoEco', 'ontoGeo', 'gml', 'geosparql']

#Useful Classes and Properties from Existing Ontologies
envo_ = {'ecosystem':'01001110', 'ecoregion':'01000276', 'wetland':'00000043', 'swamp forest':'01000432', 'shrub layer':'01000336', 'shrub area':'01000869', 'dwarf shrub area': '01000861', 'saline marsh': '00000054',
                'swamp ecosystem':'00000233', 'swamp area':'01001208', 'wetland forest':'01000893', 'habitat':'01000739'}
#pato_ = {'length':'0000122', 'area':'0001323', 'height':'0000119', 'proportion':'0001470', 'perimeter':'0001711'}
ro_ = {'has characteristic':'0000053', 'contained in':'0001018', 'has habitat':'0002303', 'visits':'0002618', 'overlaps':'0002131'}
sio_ = {'has value':'000300', 'has property': '000223', 'has part': '000028'}
ecso_ = {'ndvi':'00010076'}
#stato_ = {'kurtosis':'0000178', 'median':'0000574', 'standard deviation':'0000237', 'first_quartile':'0000167'}
snomed = {'great reed warbler':'49532004', 'occurrence':'246454002'}
rdf = {'type':'type'}
ncit_ = {'probability':'C54154', 'species':'C45293'}
bfo_ = {'has part':'0000051', 'occurs in':'0000066'}

CRSstring = "urn:ogc:def:crs:EPSG::28992"

def observationMeasurementRegion(x :float, y :float, regions :SPARQLResult) -> URIRef:
    # every ObservationRegion lies within a MeasurementRegion
    region = None
    point = Point(x, y)
    for r in regions:
        # get the polygon out of the list of coordinates
        latitudes = []
        longitudes = []
        i = 0
        for num_str in r[1].split():
            i += 1
            if i % 2 == 0:
                latitudes.append(float(num_str))
            else:
                longitudes.append(float(num_str))

        coordinates = list(zip(longitudes, latitudes))
        polygon = Polygon(coordinates)
        # check if the current point lies within the polygon or intersects it
        if point.within(polygon) or point.intersects(polygon):
            # add a "within" relationship between the point and the polygon nodes
            region = r.region
            break
    return region

def loadDataFromFile(filepath :filePath) -> pd.DataFrame:
    import pandas as pd
    # load vegetation metrics
    try:
        df = pd.read_csv(filepath)
    except:
        exit("File not found!")    
    return df

def transformToRDF(endpoint :SPARQLEndpoint, filepath :filePath, df : pd.DataFrame, classes :SPARQLResult, properties :SPARQLResult) -> list:
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))

    # initialize named graphs
    g = ds.graph(URIRef("http://www.myapp.org/ecosystem"))
    g1 = ds.graph(URIRef("http://www.myapp.org/map"))
    # parse the ahn3 graph
    g1.parse("G:/My Drive/Thesis/Output/gml_no_Bnodes_as.ttl", format="turtle")

    quads = []
    # get the bird species and the class that the df rows correspond to
    bird, row_definition = filepath.rsplit("/", 1)[-1].rsplit(".", 1)[0].rsplit("_", 1)
    row_class = ma.mapColumnToClass(row_definition, classes, False, True)
    # create the RDF instance for the current bird species
    # for Great Reed Warbler, the existing class of the snomed ontology is used as an instance
    if bird.lower() == 'grw':
        snomed = {'great reed warbler':'49532004'}
        species = SNOMED[snomed['great reed warbler']]
        species_name = "Great Reed Warbler" 
    # for Savi's Warbler, we create a custom instance, since there is no existing class
    else:
        species = MYAPP['SavisWarbler']
        species_name = "Savi's Warbler"
    # link the species to the ontoEco class
    quads.append((species, RDF.type, ontoEco['BirdSpecies'], g))
    quads.append((species, RDFS.label, Literal(species_name, datatype=XSD.string), g))
    #map df features to ontology classes
    col_classes = {}
    for column in df.columns[:-2]:
        col_classes[column] = ma.mapColumnToClass(column, classes, False, True)
    #get the measurement regions and their polygons from the map graph
    sparql = """
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX gml: <http://www.opengis.net/gml/3.2/>
    PREFIX myapp: <http://www.myapp.org/>
    PREFIX ontoGeo: <http://www.semanticweb.org/VasileiosDT/ontologies/ontoGeo/>
    SELECT DISTINCT ?region ?posList
    WHERE {
        GRAPH myapp:map {
            ?region a ontoGeo:MeasurementRegion ;
                geo:hasGeometry ?multi .
            ?multi gml:surfaceMember/gml:exterior/gml:posList ?posList .   
          } 
      }"""
    measurementRegions = ds.query(sparql)

    # Iterate over the metrics dataframe to add the metrics to the knowledge graph
    for index, row in df.iterrows():
        instances = {str(ontoEco['BirdSpecies']):species}
        # Create a unique URI for the ObservationRegion (Feature)
        row_uri = MYAPP[row_definition + "_" + bird + "_No" + str(index)]
        quads.append((row_uri, RDF.type, URIRef(row_class), g))
        instances[str(row_class)] = row_uri
        # every ObservationRegion has a Point centroid/geometry
        coords_uri = MYAPP[row_definition + "_coords_" + bird + "_No" + str(index)]
        quads.append((coords_uri, RDF.type, GML.Point, g1))
        quads.append((row_uri, GEOSPARQL.hasCentroid, coords_uri, g1))
        instances[str(GML.Point)] = coords_uri
        # relate the geometry to its coordinates and CRS
        quads.append((coords_uri, GEOSPARQL.asWKT, Literal("POINT(" + str(row['x']) + " " + str(row['y']) + ")", 
                                                               datatype=GEOSPARQL.wktLiteral), g1))
        quads.append((coords_uri, GML.srsName, Literal(CRSstring, datatype=XSD.string), g1))
        # For each metric create the appropriate instances and relate them to the right classes
        for column, value in row[:-2].items():
            col_uri = MYAPP[column + "_" + bird + '_No' + str(index)]
            quads.append((col_uri, RDF.type, URIRef(col_classes[column]), g))
            instances[str(col_classes[column])] = col_uri
        for prop in properties:
            # data properties
            if prop[2] in [XSD.float, RDFS.Literal]:
                try:
                    quads.append((instances[str(prop[0])], prop[1], 
                        Literal(row[instances[str(prop[0])].rsplit("/", 1)[-1].split("_" + bird)[0]], datatype=XSD.float), g))
                except:
                    pass  
            # object properties
            else:
                try:
                    quads.append((instances[str(prop[0])], prop[1], instances[str(prop[2])], g))
                except:
                    pass        
        region = observationMeasurementRegion(float(row['x']), float(row['y']), measurementRegions)
        quads.append((row_uri, GEOSPARQL.sfWithin, region, g1))
    return quads

def storeDataToKnowledgeBase(endpoint :SPARQLEndpoint, quads :list):
    ds = Dataset('SPARQLUpdateStore')
    try:
        ds.open((endpoint + 'sparql', endpoint + 'update'))
    except:
        exit("Could not connect to Knowledge Base. Make sure Jena Fuseki server is up and running.")
    try:
        ds.addN(quads)
    except:
        exit("Problem with storing data to Knowledge Base. Make sure the data is in the correct quads form.")

def dataIngestionBasedOnOntology(endpoint :SPARQLEndpoint, filepath :filePath):
    
    ds = Dataset('SPARQLUpdateStore')
    ds.open((endpoint + 'sparql', endpoint + 'update'))
    #Namespace prefixes
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
    
    ds.remove_graph(ds.get_context(URIRef("http://www.myapp.org/map")))
    ds.remove_graph(ds.get_context(URIRef("http://www.myapp.org/ecosystem")))
    df = loadDataFromFile(filepath)
    
    
    # get ontology classes and properties
    classes = qa.getOntologyClasses(endpoint, domain_ontologies)
    properties = qa.getOntologyProperties(endpoint, domain_ontologies)
    quads = transformToRDF(endpoint, filepath, df, classes, properties)
    storeDataToKnowledgeBase(endpoint, quads)    


#host = "localhost"
#endpoint = f"http://{host}:3030/ds/"
#filepath = './Data/GrW_observation.csv'

#import time
#start = time.time()
#dataIngestionBasedOnOntology(endpoint, filepath)
#end = time.time()

#print("Domain Data Ingestion: ", end - start)