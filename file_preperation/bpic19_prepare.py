import pandas as pd
import time, csv, os

from csv_to_eventgraph_neo4j.auxiliary_functions import convert_columns_into_camel_case

### config
input_path = '../data/BPIC19\\'
path_to_neo4j_import_directory = '../data/BPIC19/prepared\\'  # where prepared files will be stored



def CreateBPI19(input_path, path_to_neo4j_import_directory, fileName):
    csv_log = pd.read_csv(os.path.realpath(input_path + 'BPI_Challenge_2019.csv'),
                          keep_default_na=True, encoding='cp1252')  # load full log from csv
    csv_log["log"] = 'BPIC19'
    csv_log.columns = convert_columns_into_camel_case(csv_log.columns.values)

    csv_log.to_csv(path_to_neo4j_import_directory+fileName, index=True, index_label="idx")




fileName = 'BPIC19.csv'
start = time.time()
CreateBPI19(input_path, path_to_neo4j_import_directory, fileName)
end = time.time()
print("Prepared data for import in: "+str((end - start))+" seconds.") 



