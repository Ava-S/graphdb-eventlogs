import json
from abc import ABC
from typing import List, Any, Optional, Self, Union

from dataclasses import dataclass

from utilities.auxiliary_functions import replace_undefined_value, create_list
import re


@dataclass
class Class(ABC):
    label: str
    class_identifiers: List[str]
    ids: List[str]

    @classmethod
    def from_dict(cls, obj: Any) -> Optional[Self]:
        if obj is None:
            return None
        _label = obj.get("label")
        _class_identifiers = obj.get("class_identifiers")
        _ids = obj.get("ids")
        return cls(_label, _class_identifiers, _ids)


@dataclass
class Condition:  # TODO convert to abc, replace undefined values
    attribute: str
    values: List[Any]

    @classmethod
    def from_dict(cls, obj: Any, not_exist_properties=None) -> Optional[Self]:
        if obj is None:
            return None

        if not_exist_properties is None:
            not_exist_properties = ['<> null']
        _attribute = obj.get("attribute")
        _include_values = replace_undefined_value(obj.get("values"), not_exist_properties)
        return cls(_attribute, _include_values)


@dataclass
class RelationConstructorByNodes(ABC):
    from_node_label: str
    to_node_label: str
    foreign_key: str
    primary_key: str
    reversed: bool

    @classmethod
    def from_dict(cls, obj: Any) -> Optional[Self]:
        if obj is None:
            return None

        _from_node_label = obj.get("from_node_label")
        _to_node_label = obj.get("to_node_label")
        _foreign_key = obj.get("foreign_key")
        _primary_key = replace_undefined_value(obj.get("primary_key"), "ID")
        _reversed = replace_undefined_value(obj.get("reversed"), False)

        return cls(from_node_label=_from_node_label, to_node_label=_to_node_label,
                   foreign_key=_foreign_key, primary_key=_primary_key,
                   reversed=_reversed)


@dataclass()
class Node(ABC):
    node_name: str
    node_label: str
    properties: List[Any]

    @classmethod
    def from_string(cls, node_description: str) -> Optional[Self]:
        # we expect a node to be described in (node_name:Node_label)
        node_description = re.sub(r"[() ]", "", node_description)
        node_components = node_description.split(":")
        node_name = node_components[0]
        node_label = ""
        if len(node_components) > 1:
            node_label = node_components[1]
        return cls(node_name=node_name, node_label=node_label, properties=None)

    def get_node_pattern(self):
        pass


@dataclass()
class Relationship(ABC):
    relation_name: str
    relation_type: str
    from_node: Node
    to_node: Node
    properties: List[Any]
    has_direction: bool

    @classmethod
    def from_string(cls, relation_description: str, node_class: Node) -> Optional[Self]:
        # we expect a node to be described in (node_name:Node_label)
        relation_directions = {
            "left-to-right": {"has_direction": True, "from_node": 0, "to_node": 1},
            "right-to-left": {"has_direction": True, "from_node": 1, "to_node": 0},
            "undefined": {"has_direction": False, "from_node": 0, "to_node": 1}
        }

        nodes = re.findall(r'\(.*?\)', relation_description)
        _relation_string = re.findall(r'\[.*?\]', relation_description)[0]
        _relation_string = re.sub(r"[\[\]]", "", _relation_string)
        _relation_components = _relation_string.split(":")
        _relation_name = _relation_components[0]
        _relation_type = _relation_components[1]

        if ">" in relation_description:
            direction = "left-to-right"
        elif "<" in relation_description:
            direction = "right-to-left"
        else:
            direction = "undefined"

        _has_direction = relation_directions[direction]["has_direction"]
        _from_node = node_class.from_string(nodes[relation_directions[direction]["from_node"]])
        _to_node = node_class.from_string(nodes[relation_directions[direction]["to_node"]])

        return cls(relation_name=_relation_name, relation_type=_relation_type,
                   from_node=_from_node, to_node=_to_node, properties=[], has_direction=_has_direction)

    def get_relationship_pattern(self):
        pass


@dataclass
class RelationConstructorByRelations(ABC):
    antecedents: List[Relationship]
    consequent: Relationship
    from_node_name: str
    to_node_name: str
    from_node_label: str
    to_node_label: str

    @classmethod
    def from_dict(cls, obj: Any, relationship_class: Relationship, node_class: Node) -> Optional[Self]:
        if obj is None:
            return None

        _antecedents = [relationship_class.from_string(y, node_class) for y in obj.get("antecedents")]
        _consequent = relationship_class.from_string(obj.get("consequent"), node_class)

        _from_node_name = _consequent.from_node.node_name
        _to_node_name = _consequent.to_node.node_name
        _from_node_label = _consequent.from_node.node_label
        _to_node_label = _consequent.to_node.node_label

        return cls(antecedents=_antecedents, consequent=_consequent, from_node_name=_from_node_name,
                   to_node_name=_to_node_name, from_node_label=_from_node_label, to_node_label=_to_node_label)

    def get_from_node_name(self):
        return self.consequent.from_node.node_name

    def get_to_node_name(self):
        return self.consequent.to_node.node_name

    def get_from_node_label(self):
        return self.consequent.from_node.node_label

    def get_to_node_label(self):
        return self.consequent.to_node.node_label\

    def get_antecedent_query(self):
        pass


@dataclass
class RelationConstructorByQuery(ABC):
    query: str

    @classmethod
    def from_dict(cls, obj: Any) -> Optional[Self]:
        if obj is None:
            return None

        _query = obj.get("query")

        return cls(query=_query)


@dataclass
class Relation(ABC):
    include: bool
    type: str
    constructed_by: Union[RelationConstructorByNodes, RelationConstructorByRelations, RelationConstructorByQuery]
    constructor_type: str

    @classmethod
    def from_dict(cls, obj: Any, constructor_by_relation_class: RelationConstructorByRelations,
                  relationship_class: Relationship, node_class: Node) -> Optional[Self]:
        if obj is None:
            return None
        _include = replace_undefined_value(obj.get("include"), True)
        if not _include:
            return None

        _type = obj.get("type")

        _constructed_by = RelationConstructorByNodes.from_dict(obj.get("constructed_by_nodes"))
        if _constructed_by is None:
            _constructed_by = constructor_by_relation_class.from_dict(obj.get("constructed_by_relations"),
                                                                      relationship_class, node_class)
        if _constructed_by is None:
            _constructed_by = RelationConstructorByQuery.from_dict(obj.get("constructed_by_query"))

        _constructor_type = _constructed_by.__class__.__name__

        return cls(_include, _type, constructed_by=_constructed_by, constructor_type=_constructor_type)


@dataclass
class EntityConstructorByNode(ABC):
    node_label: str
    conditions: List[Condition]

    @classmethod
    def from_dict(cls, obj: Any, condition_class_name: Condition = Condition) -> Optional[Self]:
        if obj is None:
            return None

        _node_label = obj.get("node_label")
        _conditions = create_list(condition_class_name, obj.get("conditions"))

        return cls(node_label=_node_label, conditions=_conditions)


@dataclass
class EntityConstructorByRelation(ABC):
    relation_type: str
    conditions: List[Condition]

    @classmethod
    def from_dict(cls, obj: Any, condition_class_name: Condition = Condition) -> Optional[Self]:
        if obj is None:
            return None

        _relation_type = obj.get("relation_type")
        _conditions = create_list(condition_class_name, obj.get("conditions"))

        return cls(relation_type=_relation_type, conditions=_conditions)


@dataclass
class EntityConstructorByQuery(ABC):
    query: str

    @classmethod
    def from_dict(cls, obj: Any) -> Optional[Self]:
        if obj is None:
            return None

        _query = obj.get("query")

        return cls(query=_query)


@dataclass
class Entity(ABC):
    include: bool
    constructed_by: Union[EntityConstructorByNode, EntityConstructorByRelation, EntityConstructorByQuery]
    constructor_type: str
    type: str
    labels: List[str]
    primary_keys: List[str]
    all_entity_attributes: List[str]
    entity_attributes_wo_primary_keys: List[str]
    corr: bool
    df: bool
    include_label_in_df: bool
    merge_duplicate_df: bool
    delete_parallel_df: bool

    def get_primary_keys(self):
        return self.primary_keys

    @staticmethod
    def determine_labels(labels: List[str], _type: str) -> List[str]:
        if "Entity" in labels:
            labels.remove("Entity")

        if _type not in labels:
            labels.insert(0, _type)

        return labels

    def get_properties(self):
        properties = {}
        for condition in self.constructed_by.conditions:
            properties[condition.attribute] = condition.values

        return properties

    @classmethod
    def from_dict(cls, obj: Any, condition_class_name: Condition = Condition,
                  relation_class_name: Relation = Relation) -> Optional[Self]:

        if obj is None:
            return None
        _include = replace_undefined_value(obj.get("include"), True)
        if not _include:
            return None

        _constructed_by = EntityConstructorByNode.from_dict(obj.get("constructed_by_node"))
        if _constructed_by is None:
            _constructed_by = EntityConstructorByRelation.from_dict(obj.get("constructed_by_relation"))
        if _constructed_by is None:
            _constructed_by = EntityConstructorByQuery.from_dict(obj.get("constructed_by_query"))

        _constructor_type = _constructed_by.__class__.__name__
        _type = obj.get("type")
        _labels = replace_undefined_value(obj.get("labels"), [])
        _labels = Entity.determine_labels(_labels, _type)
        _primary_keys = obj.get("primary_keys")
        # entity attributes may have primary keys (or not)
        _entity_attributes = replace_undefined_value(obj.get("entity_attributes"), [])
        # create a list of all entity attributes
        _all_entity_attributes = list(set(_entity_attributes + _primary_keys))
        # remove the primary keys
        _entity_attributes_wo_primary_keys = [attr for attr in _all_entity_attributes if attr not in _primary_keys]

        _corr = _include and replace_undefined_value(obj.get("corr"), False)
        _df = _corr and replace_undefined_value(obj.get("df"), False)
        _include_label_in_df = _df and replace_undefined_value(obj.get("include_label_in_df"), False)
        _merge_duplicate_df = _df and replace_undefined_value(obj.get("merge_duplicate_df"), False)

        _delete_parallel_df = _df and obj.get("delete_parallel_df")

        return cls(include=_include, constructed_by=_constructed_by, constructor_type=_constructor_type,
                   type=_type, labels=_labels, primary_keys=_primary_keys,
                   all_entity_attributes=_all_entity_attributes,
                   entity_attributes_wo_primary_keys=_entity_attributes_wo_primary_keys,
                   corr=_corr, df=_df, include_label_in_df=_include_label_in_df, merge_duplicate_df=_merge_duplicate_df,
                   delete_parallel_df=_delete_parallel_df)


@dataclass
class Log(ABC):
    include: bool
    has: bool

    @classmethod
    def from_dict(cls, obj: Any) -> Self:
        if obj is None:
            return Log(True, True)
        _include = replace_undefined_value(obj.get("include"), True)
        if not _include:
            return None
        _has = replace_undefined_value(obj.get("has"), True)
        return cls(_include, _has)


class SemanticHeader(ABC):
    def __init__(self, name: str, version: str,
                 entities_derived_from_nodes: List[Entity], entities_derived_from_relations: List[Entity],
                 entities_derived_from_query: List[Entity],
                 relations_derived_from_nodes: List[Relation], relation_derived_from_relations: List[Relation],
                 relations_derived_from_query: List[Relation],
                 classes: List[Class], log: Log):
        self.name = name
        self.version = version

        self.entities_derived_from_nodes = entities_derived_from_nodes
        self.entities_derived_from_relations = entities_derived_from_relations
        self.entities_derived_from_query = entities_derived_from_query
        self.relations_derived_from_nodes = relations_derived_from_nodes
        self.relation_derived_from_relations = relation_derived_from_relations
        self.relations_derived_from_query = relations_derived_from_query
        self.classes = classes
        self.log = log

    def get_entity(self, entity_type) -> Optional[Entity]:
        for entity in self.entities_derived_from_nodes + self.entities_derived_from_relations + \
                      self.entities_derived_from_query:
            if entity_type == entity.type:
                return entity
        return None

    @classmethod
    def from_dict(cls, obj: Any, derived_entity_class_name: Entity = Entity,
                  reified_entity_class_name: Entity = Entity,
                  relation_class_name: Relation = Relation,
                  relation_constructor_class_name: RelationConstructorByRelations = RelationConstructorByRelations,
                  relationship_class : Relationship = Relationship,
                  node_class : Node = Node,
                  class_class_name: Class = Class, log_class_name: Log = Log) -> Optional[Self]:
        if obj is None:
            return None
        _name = obj.get("name")
        _version = obj.get("version")
        _entities = create_list(derived_entity_class_name, obj.get("entities"))
        _entities_derived_from_nodes = [entity for entity in _entities if
                                        entity.constructor_type == "EntityConstructorByNode"]
        _entities_derived_from_relations = [entity for entity in _entities if
                                            entity.constructor_type == "EntityConstructorByRelation"]
        _entities_derived_from_query = [entity for entity in _entities if
                                        entity.constructor_type == "EntityConstructorByQuery"]
        _relations = create_list(relation_class_name, obj.get("relations"), relation_constructor_class_name, relationship_class, node_class)
        _relations_derived_from_nodes = [relation for relation in _relations if
                                         relation.constructor_type == "RelationConstructorByNodes"]
        _relations_derived_from_relations = [relation for relation in _relations if
                                             "RelationConstructorByRelations" in relation.constructor_type]
        _relations_derived_from_query = [relation for relation in _relations if
                                         relation.constructor_type == "RelationConstructorByQuery"]
        _classes = create_list(class_class_name, obj.get("classes"))
        _log = log_class_name.from_dict(obj.get("log"))
        return cls(_name, _version,
                   _entities_derived_from_nodes, _entities_derived_from_relations, _entities_derived_from_query,
                   _relations_derived_from_nodes, _relations_derived_from_relations, _relations_derived_from_query,
                   _classes, _log)

    @classmethod
    def create_semantic_header(cls, dataset_name: str, **kwargs):
        with open(f'../json_files/{dataset_name}.json') as f:
            json_semantic_header = json.load(f)

        semantic_header = cls.from_dict(json_semantic_header, **kwargs)
        return semantic_header
