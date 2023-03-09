import os

import pandas as pd
import time

from utilities.auxiliary_functions import convert_columns_into_camel_case

## config
current_file_path = os.path.dirname(__file__)

input_path = os.path.join(current_file_path, '..', 'data', 'BoxProcess')
output_path = os.path.join(current_file_path, '..', 'data', 'BoxProcess', 'prepared')


def create_boxprocess():
    log = pd.read_csv(os.path.join(input_path, 'data.csv'), keep_default_na=True, sep=";", dtype={"Equipment": "Int64"})
    log.columns = convert_columns_into_camel_case(log.columns.values)
    log['log'] = 'Running Example'
    log.to_csv(os.path.join(output_path, 'data.csv'), index=True, index_label="idx")


def main():
    start = time.time()
    create_boxprocess()
    end = time.time()
    print("Prepared data for import in: " + str((end - start)) + " seconds.")


if __name__ == "__main__":
    main()
