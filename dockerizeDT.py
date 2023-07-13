from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import re
from pathlib import Path
from dotenv import load_dotenv
import queryAgents as qa
import mappingAgents as ma

endpoint = "http://localhost:3030/ds/"

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SDM_DIR = os.path.join(BASE_DIR, 'SDM')
VIS_DIR = os.path.join(BASE_DIR, 'Visualization')
DJANGO_DIR = os.path.join(BASE_DIR, 'app')
FUSEKI_DATA_DIR = os.path.join(BASE_DIR, 'fuseki-data')
FUSEKI_CONFIG_DIR = os.path.join(BASE_DIR, 'fuseki-configuration')
SDM_fileName = "api.R"
VIS_fileName = "api.R"
DB_HOST_ENV_VAR = 'MYSQL_HOST'



def getRequirementstxt():
    subprocess.run(['pip', 'freeze', '-l'], stdout=open(os.path.join(DJANGO_DIR, 'requirements.txt'), 'w'), check=True)


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

#get container names
containerList = []
containers = qa.getContainers(endpoint)
for container in containers:
    containerList.append(str(container['container']))

results = qa.getContainerImage(endpoint, ['scenario'])
for r in results:
    djangoImage = r['image']

#get django app env vars
vars = qa.getContainerEnvVar(endpoint, ['scenario'])
appHome = ma.mapInputToValue('app_home', vars)
home = ma.mapInputToValue('home', vars)
pythonVersion = ma.mapInputToValue('python_version', vars)

ports = qa.getContainerPorts(endpoint, ['scenario'])
for port in ports:
    djangoHostPort = port['hostPortValue']
    djangoContainerPort = port['containerPortValue']

#get db image
results = qa.getContainerImage(endpoint, ['mysql'])
for r in results:
    mysqlImage = r['image']

#get db env vars
results = qa.getContainerEnvVar(endpoint, ['mysql'])
database = ma.mapInputToValue('database', results, False)
user = ma.mapInputToValue('user', results, False)
password = ma.mapInputToValue('mysql_password', results)

#get db ports
ports = qa.getContainerPorts(endpoint, ['user_db'])
for port in ports:
    mysqlHostPort = port['hostPortValue']
    mysqlContainerPort = port['containerPortValue']

results = qa.getContainerImage(endpoint, ['sdm'])
for r in results:
    sdmImage = r['image']

ports = qa.getContainerPorts(endpoint, ['sdm'])
for port in ports:
    sdmHostPort = port['hostPortValue']
    sdmContainerPort = port['containerPortValue']

results = qa.getContainerImage(endpoint, ['visualization'])
for r in results:
    visImage = r['image']

ports = qa.getContainerPorts(endpoint, ['visualization'])
for port in ports:
    visHostPort = port['hostPortValue']
    visContainerPort = port['containerPortValue']

vars = qa.getContainerEnvVar(endpoint, ['fuseki'])
fusekiPassword = ma.mapInputToValue('password', vars, False)
timeout = ma.mapInputToValue('timeout', vars, False)

results = qa.getContainerImage(endpoint, ['fuseki'])
for r in results:
    fusekiImage = r['image']

# get the requirements.txt file
getRequirementstxt()

# Set up the Jinja2 environment
env = Environment(loader=FileSystemLoader('jinjaTemplates'))

# Render the Django Dockerfile template
dockerfile_template = env.get_template('djangoDocker.j2')
dockerfile = dockerfile_template.render(
    pythonVersion=pythonVersion,
    home = home,
    appHome = appHome
)

# Write the Django Dockerfile to disk
with open(os.path.join(DJANGO_DIR, 'Dockerfile'), "w") as f:
    f.write(dockerfile)

# Render the SDM API Dockerfile template
dockerfile_template = env.get_template('APIDocker.j2')
dockerfile = dockerfile_template.render(
    requirements = getRpackages(os.path.join(SDM_DIR, SDM_fileName)),
    srcFileName = SDM_fileName,
)

# Write the SDM API Dockerfile to disk
with open(os.path.join(SDM_DIR, "Dockerfile"), "w") as f:
    f.write(dockerfile)


# Render the Visualization API Dockerfile template
dockerfile_template = env.get_template('APIDocker.j2')
dockerfile = dockerfile_template.render(
    requirements = getRpackages(os.path.join(VIS_DIR, VIS_fileName)),
    srcFileName = VIS_fileName,
)

# Write the Visualization API Dockerfile to disk
with open(os.path.join(VIS_DIR, "Dockerfile"), "w") as f:
    f.write(dockerfile)

# Render the docker-compose template
dockercompose_template = env.get_template('dockerCompose.j2')
dockercompose = dockercompose_template.render(
    dbContainerName = 'user_db',
    mysqlImage = mysqlImage,
    mysqlDatabase = database,
    mysqlUser = user,
    mysqlPassword = password,
    mysqlPort = mysqlHostPort,
    sdmContainerName = "sdm",
    sdmImageName = sdmImage,
    sdmPort = sdmHostPort,
    visContainerName = "visualization",
    visImageName = visImage,
    visPort = visHostPort,
    fusekiContainerName = 'fuseki',
    fusekiImage = fusekiImage,
    fusekiAdminPassword = fusekiPassword,
    fusekiQueryTimeout = str(timeout),
    fusekiDataPath = FUSEKI_DATA_DIR,
    fusekiConfigPath = FUSEKI_CONFIG_DIR,
    djangoContainerName = 'scenario_dt',
    djangoDockerfilePath = DJANGO_DIR,
    djangoImageName = djangoImage,
    dbHostEnvVar = DB_HOST_ENV_VAR,
    djangoSourceCodePath = DJANGO_DIR,
    djangoPort = djangoHostPort,
    djangoDependencies = """- db
- fuseki"""
)

# Write the docker-compose to disk
with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(dockercompose)

