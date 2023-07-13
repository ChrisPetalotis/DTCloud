from rdflib import Dataset, URIRef, Literal, Namespace, RDF, RDFS, XSD
import os
import requests
import base64
import re

# Set up authentication
access_token = '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'

# Set the owner and name of the repository
owner = 'Vasilis421'
repo_name = 'DTCloudThesis'

# Make the API request to get the repository details
headers = {'Authorization': f'Bearer {access_token}'}

def getRpackages(filePath, r_script=None):
    # Define regular expressions to match library() and require() statements
    library_pattern = re.compile(r"\s*library\(([\w\.]+)\)")
    require_pattern = re.compile(r"\s*require\(([\w\.]+)\)")
    # Read the R script into a string
    if r_script is None:
        with open(filePath, "r") as f:
            r_script = f.read()
    # Find all library() and require() statements in the R script
    library_matches = library_pattern.findall(r_script)
    require_matches = require_pattern.findall(r_script)
    # Remove duplicates
    library_matches = list(set(library_matches))
    require_matches = list(set(require_matches))
    # Remove plumber
    if 'plumber' in library_matches:
        library_matches.remove('plumber')
    if 'plumber' in require_matches:
        require_matches.remove('plumber')
    # Combine the two lists
    r_packages = library_matches + require_matches
    # Remove duplicates again
    r_packages = list(set(r_packages))
    result = ", ".join([f'"{item}"' for item in r_packages])
    return result

def get_folder_paths(repo_owner, repo_name, headers, path='', level=0):
    # Set the GitHub API base URL
    base_url = 'https://api.github.com'

    # Construct the API endpoint URL
    api_url = f'{base_url}/repos/{repo_owner}/{repo_name}/contents/{path}'

    
    # Send GET request to the API endpoint
    response = requests.get(api_url, headers=headers)

    
    # Check if the request was successful
    if response.status_code == 200:
        # Get the response JSON data
        data = response.json()
        # List to store folder paths
        folder_paths = []
        # Process each item in the response data
        for item in data:
            # Check if the item is a directory and the level is less than 2
            if item['type'] == 'dir' and level < 2:
                # Add the folder path to the list
                folder_paths.append(item['path'])
                # Recursively get folder paths from the subdirectory
                subdirectory_paths = get_folder_paths(repo_owner, repo_name, headers, item['path'], level + 1)
                # Add the subdirectory folder paths to the list
                folder_paths.extend(subdirectory_paths)
            if item['type'] == 'file' and 'requirements.txt' in item['path'].lower():
                folder_paths.append(item['path'])
            if item['type'] == 'file' and '.py' in item['path']:
                folder_paths.append(item['path'])
            if item['type'] == 'file' and '.R' in item['path']:
                folder_paths.append(item['path'])

        return folder_paths
    else:
        # Print the error message if the request failed
        print(f'Request failed with status code {response.status_code}: {response.text}')
        return []


# Get the folder paths within two nested levels
folder_paths = get_folder_paths(owner, repo_name, headers)
    
def get_file_content(repo_owner, repo_name, headers, file_path):
    # Set the GitHub API base URL
    base_url = 'https://api.github.com'

    # Construct the API endpoint URL
    api_url = f'{base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}'

    # Send GET request to retrieve file content
    response = requests.get(api_url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        file = response.json()
        # If a runtime.txt file exists, check if it specifies the Python version
        runtime_url = file["download_url"]
        runtime_response = requests.get(runtime_url, headers=headers)
        runtime_response.raise_for_status()

        content = runtime_response.text
        return content

    # Print the error message if the request failed
    print(f'Request failed with status code {response.status_code}: {response.text}')
    return None

def ingestServices(endpoint):
    response = requests.get(f'https://api.github.com/repos/{owner}/{repo_name}/languages', headers=headers)
    languages = response.json()

    MYAPP = Namespace("http://www.myapp.org/")
    ontoFlow = Namespace("http://www.semanticweb.org/VasileiosDT/ontologies/ontoFlow/")

    endpoint_update = endpoint+"update"
    endpoint_query = endpoint+"sparql"
    #endpoint = "http://localhost:3030/ds/"
    ds = Dataset("SPARQLUpdateStore")
    ds.open((endpoint_query, endpoint_update))
    ds.remove_graph(ds.get_context(URIRef("http://www.myapp.org/service")))
    graph = ds.graph(URIRef("http://www.myapp.org/service"))
    quads = []
    for path in folder_paths:
        if 'settings.py' in path:
            djangoRoot = path.split('/')[0]
            service = path.split('/')[1]
            quads.append((MYAPP[service], RDF.type, ontoFlow.ScenarioFramework, graph))
            quads.append((MYAPP[service], ontoFlow.hasName, Literal('What-if Scenario Framework', datatype=XSD.string), graph))
            quads.append((MYAPP[service], ontoFlow.hasDescription, Literal('A Service for what-if analysis, where alternative scenarios can be configured, executed, and compared.', datatype=XSD.string), graph))
            quads.append((MYAPP[service], ontoFlow.hasRootDir, Literal(djangoRoot, datatype=XSD.string), graph))
            quads.append((MYAPP[service], ontoFlow.hasLanguage, Literal('Python', datatype=XSD.string), graph))
            for djangoPath in folder_paths:
                if djangoRoot in djangoPath and 'requirements.txt' in djangoPath.lower():
                    quads.append((MYAPP[path.split('/')[1]], ontoFlow.hasRequirements, Literal(djangoPath, datatype=XSD.string), graph))
                    requirements = get_file_content(owner, repo_name, headers, djangoPath)
                    if 'mysql-con' in requirements.lower():
                        mysqlVersion = requirements.split('mysql-connector-python==')[1].split('\n')[0]
            file_content = get_file_content(owner, repo_name, headers, path)
            db = file_content.split('DATABASES = {')[1].split('}')[0]
            if 'mysql' in db.lower():
                quads.append((MYAPP['user_db'], RDF.type, ontoFlow.DB, graph))
                quads.append((MYAPP['user_db'], ontoFlow.hasName, Literal('MySQL User Database', datatype=XSD.string), graph))
                quads.append((MYAPP['user_db'], ontoFlow.hasDescription, Literal('A MySQL Database for user credentials, such as usernames and passwords.', datatype=XSD.string), graph))
            elif 'sqlite' in db.lower():
                quads.append((MYAPP['user_db'], RDF.type, ontoFlow.DB, graph))
                quads.append((MYAPP['user_db'], ontoFlow.hasName, Literal('sqlite', datatype=XSD.string), graph))
            elif 'postgresql' in db.lower():
                quads.append((MYAPP['user_db'], RDF.type, ontoFlow.DB, graph))
                quads.append((MYAPP['user_db'], ontoFlow.hasName, Literal('postgresql', datatype=XSD.string), graph))
        if '.R' in path:
            service = path.split('/')[0]
            if 'sdm' in path.lower():
                quads.append((MYAPP[service], RDF.type, ontoFlow.SimulationService, graph))
                quads.append((MYAPP[service], ontoFlow.hasName, Literal('Species Distribution Model (SDM) Simulation Service', datatype=XSD.string), graph))
                quads.append((MYAPP[service], ontoFlow.hasDescription, Literal('A service that uses an SDM to simulate the behavior of the physical system.', datatype=XSD.string), graph))
            
            elif 'visualization' in path.lower():
                quads.append((MYAPP[service], RDF.type, ontoFlow.VisualizationService, graph))
                quads.append((MYAPP[service], ontoFlow.hasName, Literal('Map Visualization Service', datatype=XSD.string), graph))
                quads.append((MYAPP[service], ontoFlow.hasDescription, Literal('A Service that is used for the visualization of the SDM results in a map of the region.', datatype=XSD.string), graph))
            quads.append((MYAPP[service], ontoFlow.hasLanguage, Literal('R', datatype=XSD.string), graph))
            quads.append((MYAPP[service], ontoFlow.hasRootDir, Literal(service, datatype=XSD.string), graph))
            file_content = get_file_content(owner, repo_name, headers, path)
            reqs = getRpackages(path, file_content)
            quads.append((MYAPP[service], ontoFlow.hasRequirements, Literal(reqs, datatype=XSD.string), graph))
        #if 'fuseki' in path.lower():
    service = 'fuseki'
    quads.append((MYAPP[service], RDF.type, ontoFlow.KB, graph))
    quads.append((MYAPP[service], ontoFlow.hasName, Literal('Jena-Fuseki Knowledge Base', datatype=XSD.string), graph))
    quads.append((MYAPP[service], ontoFlow.hasDescription, Literal('A Jena Fuseki Triple Store, that stores data in the RDF format and provides an endpoint that can be queried using SPARQL.', datatype=XSD.string), graph))
            #if 'data' in path.lower():
    path = 'fuseki-data'
    quads.append((MYAPP[service], ontoFlow.hasDataDir, Literal(path, datatype=XSD.string), graph))
            #elif 'config' in path.lower():
    path = 'fuseki-configuration'
    quads.append((MYAPP[service], ontoFlow.hasConfigDir, Literal(path, datatype=XSD.string), graph))
    ds.addN(set(quads))