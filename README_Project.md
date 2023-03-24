# Using Graph Databases to Infer Missing Case Identifiers in Event Data

## Description

This repository collects queries for modeling and importing incomplete event data as Event Knowledge Graphs using the Labeled
Property Graph data model of graph databases. Missing case identifiers are inferred using context knowledge of activities and its locations.
All scripts and queries are licensed under LGPL v3.0, see LICENSE.
Copyright information is provided within each Project.

## Requirements

### Neo4j
Install neo4j-python-driver
pip install neo4j
OR
conda install -c conda-forge neo4j-python-driver

Install Neo4j from https://neo4j.com/download/

- Neo4j Desktop https://neo4j.com/download-center/#desktop (recommended), or
- Neo4j Community Server, https://neo4j.com/download-center/#community

### Other packages
- numpy
- pandas
- tabulate
- tqdm

## Get started

### Create a new graph database

- The scripts in this release assume password "1234".
- The scripts assume the server to be available at the default URL bolt://localhost:7687
- You can modify this also in the script.
- ensure to allocate enough memory to your database, advised: dbms.memory.heap.max_size=5G
- the script expects the Neo4j APOC library to be installed as a plugin, see https://neo4j.com/labs/apoc/

How to use
----------

For data import & inference

1. start the Neo4j server
1. run main.py

## Projects

The following projects are part of this repository

### Missing Case Identifiers Inference

Method to infer missing case identifiers in event data by exploiting knowledge about the activities and their locations.


### semantic header (json files)
First version for semantic header for system/event knowledge graphs: https://multiprocessmining.org/2022/10/26/data-storage-vs-data-semantics-for-object-centric-event-data/

### event knowledge graphs

Data model and generic query templates for translating and integrating a set of related CSV event logs into single event
graph over multiple behavioral dimensions, stored as labeled property graph in [Neo4J](https://neo4j.com/).
See [csv_to_eventgraph_neo4j/README.txt](ekg_creator/README.txt)

Publications:

- Stefan Esser, Dirk Fahland: Multi-Dimensional Event Data in Graph
  Databases. [CoRR abs/2005.14552](https://arxiv.org/abs/2005.14552), [Journal on Data Semantics, DOI: 10.1007/s13740-021-00122-1](https://dx.doi.org/10.1007/s13740-021-00122-1) (
  2020)
- Esser, Stefan. (2020, February 19). A Schema Framework for Graph Event Data. Master thesis. Eindhoven University of
  Technology. https://doi.org/10.5281/zenodo.3820037

## Data set & scripts
We provide data and scripts for the running box process example

#### Datasets

- event_data.csv - contains the data of the running example for all four different variants
- activity_records.csv - contains context knowledge about the activities of the box process
- location_records - contains context knowledge about locations and information about the activities that happen at these locations to create the [:AT] relation. 

There is no separate file to create the [:AT] relationship between Activities and Locations. Instead, we add the activities directly to the location records and
for each unique primary key (name, partOf) we collect the activity names in a list and store this list as attribute. 
Then we use the activity names as foreign keys to create the [:AT] relation.

#### JSON files
- BoxProcess.json - a description of which Entities (Box), Relations (:PART_OF, :CORR, :AT, :IS), Classes need to be created:
The main script uses this information to construct the EKG.
- BoxProccess_DS.json - a description of the different data sets. It describes which labels the records should receive (e.g. :Event, :Location, :Activity) and what properties records have 

### Main script
There is one script that creates the Event/System knowledge graph: **ekg_creator/main.py**

Then there are several other scripts that support this main script
#### Data_managers

- data_managers/datastructures.py --> transforms the JSON file describing the different datasets into a class + additional methods
- data_managers/semantic_header.py --> transforms the JSON file describing the semantic header into a class + additional methods
- data_managers/interpreters.py --> Class that contains information about in what query language the semantic header and data structures should be interpreter


#### Database_managers
- database_managers/authentication.py  --> class containing the credentials to create connection to database. Local credentials are includes.
In case you want to create a remote connection, add the following piece of code to a (gitignored) file.
```python
remote = Credentials(
    uri="[your_uri]",
    user="neo4j",
    password="[your_password]"
)
```
- database_managers/db_connection.py --> class responsible for making the connection to the database and to communicate with the database
- database_managers/EventKnowledgeGraph.py --> class responsible for making (changes to) the EKG and to request data from the EKG. Makes use of several modules.

#### EKG_Modules
- ekg_modules/db_management.py --> general module to manage the database 
- ekg_modules/data_importer.py --> imports the data stored in the records into the EKG
- ekg_modules/ekg_builder_semantic_header.py --> creates the required nodes and relations as specified in the semantic header
- ekg_modules/inference_engine.py --> module responsible for inferring missing information

#### CypherQueries
Contains repeatable pieces of Cypher Queries for all necessary parts. 
- cypher_queries/query_translators --> translate semantic header and data structures into Cypher
- cypher_queries/query_library --> contains all cypher queries for the EKG modules





