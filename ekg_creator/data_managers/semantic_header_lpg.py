from dataclasses import dataclass
from typing import Optional, Any, Self

from data_managers.semantic_header import SemanticHeader, Entity, Relation, Class, Log, Condition


@dataclass
class ConditionLPG(Condition):
    @classmethod
    def from_dict(cls, obj: Any, not_exist_properties=None) -> Optional[Self]:
        if not_exist_properties is None:
            not_exist_properties = ["IS NOT NULL", '<> "nan"', '<> "None"']
        return super().from_dict(obj, not_exist_properties)

    def get_values(self):
        if self.values != ["IS NOT NULL", '<> "nan"', '<> "None"']:
            return [f'''= "{include_value}"''' for include_value in self.values]


class RelationLPG(Relation):
    pass




class SemanticHeaderLPG(SemanticHeader):
    @classmethod
    def from_dict(cls, obj: Any, interpreter: Any, derived_entity_class_name: Entity = Entity,
                  reified_entity_class_name: Entity = Entity,
                  relation_class_name: Relation = RelationLPG,
                  class_class_name: Class = Class,
                  log_class_name: Log = Log) -> Optional[Self]:
        return super().from_dict(obj,
                                 interpreter=interpreter,
                                 derived_entity_class_name=derived_entity_class_name,
                                 reified_entity_class_name=reified_entity_class_name,
                                 relation_class_name=relation_class_name,
                                 class_class_name=class_class_name,
                                 log_class_name=log_class_name)
