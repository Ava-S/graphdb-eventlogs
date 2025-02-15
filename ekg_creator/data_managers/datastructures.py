import json
import os
import warnings
import random

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pandas import DataFrame

from utilities.auxiliary_functions import replace_undefined_value, create_list


@dataclass
class DatetimeObject:
    format: str
    timezone_offset: str
    convert_to: str
    is_epoch: bool
    unit: str

    @staticmethod
    def from_dict(obj: Any) -> 'DatetimeObject':
        if obj is None:
            return None
        _format = obj.get("format")
        _timezone_offset = replace_undefined_value(obj.get("timezone_offset"), "")
        _convert_to = str(obj.get("convert_to"))
        _is_epoch = replace_undefined_value(obj.get("is_epoch"), False)
        _unit = obj.get("unit")
        return DatetimeObject(_format, _timezone_offset, _convert_to, _is_epoch, _unit)


@dataclass
class Column:
    name: str
    dtype: str
    nan_values: List[str]
    mandatory: bool
    range_start: int
    range_end: int

    @staticmethod
    def from_dict(obj: Any) -> Optional['Column']:
        if obj is None:
            return None
        _name = obj.get("name")
        _dtype = obj.get("dtype")
        _nan_values = replace_undefined_value(obj.get("nan_values"), [])
        _mandatory = replace_undefined_value(obj.get("mandatory"), True)
        _range_start = obj.get("range_start")
        _range_end = obj.get("range_end")
        _mandatory = replace_undefined_value(obj.get("mandatory"), True)
        return Column(_name, _dtype, _nan_values, _mandatory, _range_start, _range_end)


@dataclass
class Attribute:
    name: str
    columns: List[Column]
    separator: str
    is_datetime: bool
    is_compound: bool
    mandatory: bool
    datetime_object: DatetimeObject
    na_rep_value: Any
    na_rep_columns: List[Column]
    filter_exclude_values: List[str]
    filter_include_values: List[str]
    use_filter: bool
    is_primary_key: bool
    is_foreign_key: bool

    @staticmethod
    def from_dict(obj: Any) -> Optional['Attribute']:
        if obj is None:
            return None
        _name = obj.get("name")
        _columns = create_list(Column, obj.get("columns"))
        _is_compound = len(_columns) > 1
        _mandatory = bool(obj.get("mandatory"))
        _datetime_object = DatetimeObject.from_dict(obj.get("datetime_object"))
        _is_datetime = _datetime_object is not None
        _na_rep_value = obj.get("na_rep_value")
        _na_rep_columns = create_list(Column, obj.get("na_rep_columns"))
        _separator = obj.get("separator")
        _filter_exclude_values = obj.get("filter_exclude_values")
        _filter_include_values = obj.get("filter_include_values")
        _use_filter = _filter_include_values is not None or _filter_exclude_values is not None  # default value
        _use_filter = replace_undefined_value(obj.get("use_filter"), _use_filter)
        _is_primary_key = replace_undefined_value(obj.get("is_primary_key"), False)
        _is_foreign_key = replace_undefined_value(obj.get("is_foreign_key"), False)
        return Attribute(name=_name, mandatory=_mandatory, columns=_columns, separator=_separator,
                         is_compound=_is_compound,
                         is_datetime=_is_datetime, datetime_object=_datetime_object,
                         na_rep_value=_na_rep_value, na_rep_columns=_na_rep_columns,
                         filter_exclude_values=_filter_exclude_values, filter_include_values=_filter_include_values,
                         use_filter=_use_filter, is_primary_key=_is_primary_key, is_foreign_key=_is_foreign_key)


@dataclass
class Sample:
    file_name: str
    use_random_sample: bool
    population_column: str
    size: int
    ids: List[Any]

    @staticmethod
    def from_dict(obj: Any) -> Optional['Sample']:
        if obj is None:
            return None
        _file_name = obj.get("file_name")
        _use_random_sample = obj.get("use_random_sample")
        _population_column = obj.get("population_column")
        _size = obj.get("size")
        _ids = obj.get("ids")

        return Sample(_file_name, _use_random_sample, _population_column, _size, _ids)


class DataStructure:
    def __init__(self, include: bool, name: str, file_directory: str, file_names: List[str], seperator: str,
                 labels: List[str], true_values: List[str],
                 false_values: List[str], samples: Dict[str, Sample], attributes: List[Attribute]):
        self.include = include
        self.name = name
        self.file_directory = file_directory
        self.file_names = file_names
        self.seperator = seperator
        self.labels = labels
        self.true_values = true_values
        self.false_values = false_values
        self.samples = samples
        self.attributes = attributes

    def is_event_data(self):
        return "Event" in self.labels

    @staticmethod
    def from_dict(obj: Any) -> Optional['DataStructure']:
        if obj is None:
            return None

        _include = replace_undefined_value(obj.get("include"), True)

        if not _include:
            return None

        _name = obj.get("name")
        _file_directory = os.path.join(*obj.get("file_directory").split("\\"))
        _file_names = obj.get("file_names")
        _seperator = replace_undefined_value(obj.get("seperator"), ",")
        _labels = obj.get("labels")
        _true_values = obj.get("true_values")
        _false_values = obj.get("false_values")
        _samples = create_list(Sample, obj.get("samples"))
        _samples = {sample.file_name: sample for sample in _samples}
        _attributes = create_list(Attribute, obj.get("attributes"))
        return DataStructure(_include, _name, _file_directory, _file_names, _seperator,
                             _labels, _true_values, _false_values, _samples, _attributes)

    def get_primary_keys(self):
        return [attribute.name for attribute in self.attributes if attribute.is_primary_key]

    def get_foreign_keys(self):
        return [attribute.name for attribute in self.attributes if attribute.is_foreign_key]

    def get_dtype_dict(self):
        dtypes = {}
        for attribute in self.attributes:
            for column in attribute.columns:
                if column.dtype is not None:
                    if column.name not in dtypes:
                        dtypes[column.name] = column.dtype
                    elif column.dtype != dtypes[column.name]:
                        warnings.warn(
                            f"Multiple dtypes ({column.dtype} != {dtypes[column.name]}) "
                            f"defined for {column.name}")
        return dtypes

    def get_required_columns(self):
        required_columns = set()
        for attribute in self.attributes:
            # add column names to the required columns
            required_columns.update([x.name for x in attribute.columns])

        return list(required_columns)

    def create_sample(self, file_name, df_log):
        if self.samples is None:
            warnings.warn(f"No sample population has been defined for {self.name}")

        if file_name not in self.samples:
            # TODO make error
            warnings.warn(f"No sample population has been defined for {file_name}")

        sample = self.samples[file_name]
        sample_column = sample.population_column
        if sample.use_random_sample:
            random_selection = random.sample(df_log[sample_column].unique().tolist(), k=sample.size)
        else:
            random_selection = sample.ids

        df_log = df_log[df_log[sample_column].isin(random_selection)]

        return df_log

    @staticmethod
    def replace_nan_values_based_on_na_rep_columns(df_log, attribute):
        if len(attribute.na_rep_columns) != len(attribute.columns):
            # TODO make error
            warnings.warn(
                f"Na_rep_columns does not have the same size as columns for attribute {attribute.name}")
        else:  # they are the same size
            for i, na_rep_column in zip(range(len(attribute.na_rep_columns)), attribute.na_rep_columns):
                attribute_name = f"{attribute.name}_{i}"
                df_log[attribute_name].fillna(df_log[na_rep_column.name], inplace=True)

        return df_log

    @staticmethod
    def replace_nan_values_based_on_na_rep_value(df_log, attribute):
        for i in range(len(attribute.columns)):
            attribute_name = f"{attribute.name}_{i}"
            df_log[attribute_name].fillna(attribute.na_rep_value, inplace=True)

        return df_log

    @staticmethod
    def replace_nan_values_with_unknown(df_log, attribute):
        column: Column
        for i, column in zip(range(len(attribute.columns)), attribute.columns):
            attribute_name = f"{attribute.name}_{i}"
            if column.mandatory:
                try:
                    df_log[attribute_name].fillna("Unknown", inplace=True)
                except:
                    df_log[attribute_name].fillna(-1, inplace=True)
        return df_log

    @staticmethod
    def create_compound_attribute(df_log, attribute):
        compound_column_names = [x.name for x in attribute.columns]
        df_log[attribute.name] = df_log[compound_column_names].apply(
            lambda row: attribute.separator.join([value for value in row.values.astype(str) if
                                                  not (value == 'nan' or value != value)]), axis=1)
        return df_log

    @staticmethod
    def combine_attribute_columns(df_log, attribute):
        compound_attribute_names = [f"{attribute.name}_{i}" for i in range(len(attribute.columns))]
        if attribute.is_compound:
            df_log[f"{attribute.name}_attribute"] = df_log[compound_attribute_names].apply(
                lambda row: attribute.separator.join([value for value in row.values.astype(str) if
                                                      not (value == 'nan' or value != value)]), axis=1)
        else:
            df_log[f"{attribute.name}_attribute"] = df_log[f"{attribute.name}_0"]
        df_log = df_log.drop(columns=compound_attribute_names)
        return df_log

    @staticmethod
    def create_attribute_columns(df_log, attribute):
        for i, column in zip(range(len(attribute.columns)), attribute.columns):
            attribute_name = f"{attribute.name}_{i}"
            df_log[attribute_name] = df_log[column.name]
            if column.range_start is not None or column.range_end is not None:
                df_log[attribute_name] = df_log[attribute_name].str[column.range_start:column.range_end]
                df_log[attribute_name] = pd.to_numeric(df_log[attribute_name], errors='ignore')
        return df_log

    @staticmethod
    def replace_with_nan(df_log, attribute):
        for i, column in zip(range(len(attribute.columns)), attribute.columns):
            attribute_name = f"{attribute.name}_{i}"
            for nan_value in column.nan_values:
                df_log[attribute_name] = df_log[attribute_name].replace(nan_value, np.nan, regex=False)
        return df_log

    def preprocess_according_to_attributes(self, df_log):
        # loop over all attributes and check if they should be created, renamed or imputed
        for attribute in self.attributes:
            df_log = DataStructure.create_attribute_columns(df_log, attribute)
            df_log = DataStructure.replace_with_nan(df_log, attribute)
            if len(attribute.na_rep_columns) > 0:  # impute values in case of missing values
                df_log = DataStructure.replace_nan_values_based_on_na_rep_columns(df_log, attribute)
            if attribute.na_rep_value is not None:
                df_log = DataStructure.replace_nan_values_based_on_na_rep_value(df_log, attribute)
            if attribute.mandatory:
                df_log = DataStructure.replace_nan_values_with_unknown(df_log, attribute)
            df_log = DataStructure.combine_attribute_columns(df_log, attribute)

        return df_log

    def prepare_event_data_sets(self, input_path, file_name, use_sample):
        dtypes = self.get_dtype_dict()
        required_columns = self.get_required_columns()

        true_values = self.true_values
        false_values = self.false_values

        df_log: DataFrame = pd.read_csv(os.path.join(input_path, file_name), keep_default_na=True,
                                        usecols=required_columns, dtype=dtypes, true_values=true_values,
                                        false_values=false_values, sep=self.seperator)

        if use_sample and self.is_event_data():
            df_log = self.create_sample(file_name, df_log)

        df_log = self.preprocess_according_to_attributes(df_log)

        # all columns have been renamed to or constructed with the name attribute,
        # hence only keep those that match with a name attribute
        required_attributes = list([f"{attribute.name}_attribute" for attribute in self.attributes])
        required_attributes_mapping = {f"{attribute.name}_attribute": f"{attribute.name}" for attribute in
                                       self.attributes}
        df_log = df_log[required_attributes]
        df_log = df_log.rename(columns=required_attributes_mapping)

        return df_log

    def get_datetime_formats(self) -> Dict[str, DatetimeObject]:
        datetime_formats = {}

        for attribute in self.attributes:
            if attribute.is_datetime:
                datetime_formats[attribute.name] = attribute.datetime_object

        return datetime_formats

    def get_attribute_value_pairs_filtered(self, exclude: bool = True) -> Dict[str, List[str]]:
        attribute_value_pairs = {}

        for attribute in self.attributes:
            if attribute.use_filter:
                attribute_value_pairs[attribute.name] \
                    = attribute.filter_exclude_values if exclude else attribute.filter_include_values

        return attribute_value_pairs


class ImportedDataStructures:
    def __init__(self, dataset_name):
        random.seed(1)
        with open(f'../json_files/{dataset_name}_DS.json') as f:
            json_event_tables = json.load(f)

        self.structures = [DataStructure.from_dict(item) for item in json_event_tables]
        self.structures = [item for item in self.structures if item is not None]
