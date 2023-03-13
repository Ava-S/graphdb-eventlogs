from data_managers.semantic_header import Entity
from database_managers.db_connection import DatabaseConnection
from utilities.performance_handling import Performance
from database_managers.query_library import CypherQueryLibrary
from data_managers.semantic_header_lpg import SemanticHeaderLPG, RelationLPG


class EKGUsingSemanticHeaderBuilder:
    def __init__(self, db_connection: DatabaseConnection, semantic_header: SemanticHeaderLPG, batch_size: int,
                 perf: Performance):
        self.connection = db_connection
        self.semantic_header = semantic_header
        self.batch_size = batch_size
        self.perf = perf

    def _write_message_to_performance(self, message: str):
        if self.perf is not None:
            self.perf.finished_step(activity=message)

    def create_log(self):
        if self.semantic_header.log.include:
            self.connection.exec_query(CypherQueryLibrary.get_create_log_query)
            self._write_message_to_performance(message="Creation of (:Log) nodes")

            if self.semantic_header.log.has:
                self.connection.exec_query(CypherQueryLibrary.get_link_events_to_log_query,
                                           **{"batch_size": self.batch_size})
                self._write_message_to_performance(message="Creation of (:Event) <- [:HAS] - (:Log) relation")

    def create_entities(self, node_label) -> None:
        entity: Entity
        for entity in self.semantic_header.entities_derived_from_nodes:
            if node_label is None or entity.constructed_by.node_label == node_label:
                self.connection.exec_query(CypherQueryLibrary.get_create_entity_query, **{"entity": entity})
                self._write_message_to_performance(f"Entity (:{entity.get_label_string()}) node created")

    def correlate_events_to_entities(self, node_label) -> None:
        # correlate events that contain a reference from an entity to that entity node
        entity: Entity
        for entity in self.semantic_header.entities_derived_from_nodes:
            if entity.corr and (node_label is None or entity.constructed_by.node_label == node_label):
                # find events that contain the entity as property and not nan
                # save the value of the entity property as id and also whether it is a virtual entity
                # create a new entity node if it not exists yet with properties
                self.connection.exec_query(CypherQueryLibrary.get_correlate_events_to_entity_query,
                                           **{"entity": entity, "batch_size": self.batch_size})

                self._write_message_to_performance(
                    f"Relation (:Event) - [:CORR] -> (:{entity.get_label_string()}) created")

    def create_entity_relations(self) -> None:
        # find events that are related to different entities of which one event also has a reference to the other entity
        # create a relation between these two entities
        relation: RelationLPG
        for relation in self.semantic_header.relations:
            if relation.include:
                self.create_foreign_nodes(relation)
                self.connection.exec_query(CypherQueryLibrary.get_create_entity_relationships_query,
                                           **{"relation": relation,
                                              "batch_size": self.batch_size})
                self.delete_foreign_nodes(relation)

                self._write_message_to_performance(
                    message=f"Relation (:{relation.from_node_label}) - [:{relation.type}] -> "
                            f"(:{relation.to_node_label}) done")

    def create_foreign_nodes(self, relation: RelationLPG):
        self.connection.exec_query(CypherQueryLibrary.create_foreign_key_relation,
                                   **{"relation": relation})
        self.connection.exec_query(CypherQueryLibrary.merge_foreign_key_nodes,
                                   **{"relation": relation})

    def delete_foreign_nodes(self, relation: RelationLPG):
        self.connection.exec_query(CypherQueryLibrary.get_delete_foreign_nodes_query,
                                   **{"relation": relation})


    def create_entities_by_relations(self) -> None:
        relation: RelationLPG
        entity: Entity
        for entity in self.semantic_header.entities_derived_from_relations:
            if entity.include:
                self.connection.exec_query(CypherQueryLibrary.get_create_entities_by_relations_query,
                                           **{"entity": entity})

                self.connection.exec_query(CypherQueryLibrary.get_add_reified_relation_query,
                                           **{"entity": entity, "batch_size": self.batch_size})
                self._write_message_to_performance(
                    message=f"Relation [:{entity.type.upper()}] reified as "
                            f"(:Entity:{entity.get_label_string()}) node")

    def correlate_events_to_reification(self) -> None:
        reified_entity: Entity
        for reified_entity in self.semantic_header.entities_derived_from_relations:
            if reified_entity.corr:
                reified_entity_labels = reified_entity.get_label_string()
                # correlate events that are related to an entity which is reified into a new entity
                # to the new reified entity

                self.connection.exec_query(CypherQueryLibrary.get_correlate_events_to_reification_query,
                                           **{"reified_entity": reified_entity})

                self._write_message_to_performance(
                    f"Relation (:Event) - [:CORR] -> (:Entity:{reified_entity_labels}) created")

    def create_df_edges(self) -> None:
        entity: Entity

        for entity in self.semantic_header.entities_derived_from_nodes:
            if entity.df:
                self.connection.exec_query(CypherQueryLibrary.get_create_directly_follows_query,
                                           **{"entity": entity, "batch_size": self.batch_size})
                self._write_message_to_performance(f"Created [:DF] edge for (:{entity.get_label_string()})")

        for entity in self.semantic_header.entities_derived_from_relations:
            if entity.df:
                self.connection.exec_query(CypherQueryLibrary.get_create_directly_follows_query,
                                           **{"entity": entity, "batch_size": self.batch_size})
                self._write_message_to_performance(
                    f"Created [:DF] edge for (:{entity.get_label_string()})")

    def merge_duplicate_df(self):
        entity: Entity
        for entity in self.semantic_header.entities_derived_from_nodes:
            if entity.merge_duplicate_df:
                self.connection.exec_query(CypherQueryLibrary.get_merge_duplicate_df_entity_query, **{"entity": entity})
                self.perf.finished_step(
                    activity=f"Merged duplicate [:DF] edges for (:{entity.get_label_string()}) done")

    def delete_parallel_dfs_derived(self):
        reified_entity: Entity
        original_entity: Entity
        relation: RelationLPG
        for reified_entity in self.semantic_header.entities_derived_from_relations:
            if reified_entity.delete_parallel_df:
                relation = reified_entity.relation
                parent_entity = self.semantic_header.get_entity(relation.from_node_label)
                child_entity = self.semantic_header.get_entity(relation.to_node_label)
                for original_entity in [parent_entity, child_entity]:
                    self.connection.exec_query(CypherQueryLibrary.delete_parallel_directly_follows_derived,
                                               **{"reified_entity": reified_entity,
                                                  "original_entity": original_entity})
                    self._write_message_to_performance(
                        f"Deleted parallel DF of (:{reified_entity.get_label_string()}) and (:{original_entity.get_label_string()})")

    def create_classes(self):
        classes = self.semantic_header.classes
        for _class in classes:
            self.connection.exec_query(CypherQueryLibrary.get_create_class_query, **{"_class": _class})
            self.connection.exec_query(CypherQueryLibrary.get_link_event_to_class_query,
                                       **{"_class": _class, "batch_size": self.batch_size})

    def create_static_nodes_and_relations(self):
        # TODO no implementation yet (see if needed)
        self._write_message_to_performance("Static Nodes and Relations are created")

    def add_attributes_to_classifier(self, relation, label, properties, copy_as):
        self.connection.exec_query(CypherQueryLibrary.add_attributes_to_classifier,
                                   **{"relation": relation, "label": label, "properties": properties,
                                      "copy_as": copy_as})
