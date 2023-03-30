import os

from data_managers.interpreters import Interpreter
from data_managers.semantic_header import SemanticHeader
from database_managers.EventKnowledgeGraph import EventKnowledgeGraph, DatabaseConnection
from data_managers.datastructures import ImportedDataStructures
from utilities.performance_handling import Performance
from database_managers import authentication

connection = authentication.connections_map[authentication.Connections.LOCAL]

dataset_name = 'BoxProcess'

query_interpreter = Interpreter("Cypher")
semantic_header = SemanticHeader.create_semantic_header(dataset_name, query_interpreter)
perf_path = os.path.join("..", "perf", dataset_name, f"{dataset_name}Performance.csv")
number_of_steps = 35

datastructures = ImportedDataStructures(dataset_name)

# several steps of import, each can be switch on/off
step_clear_db = True
step_populate_graph = True
verbose = False  # print the used queries

db_connection = DatabaseConnection(db_name=connection.user, uri=connection.uri, user=connection.user,
                                   password=connection.password, verbose=verbose)


def create_graph_instance(perf: Performance) -> EventKnowledgeGraph:
    """
    Creates an instance of an EventKnowledgeGraph
    @return: returns an EventKnowledgeGraph
    """

    return EventKnowledgeGraph(db_connection=db_connection, db_name=connection.user,
                               event_tables=datastructures, semantic_header=semantic_header, perf=perf)


def clear_graph(graph: EventKnowledgeGraph, perf: Performance) -> None:
    """
    # delete all nodes and relations in the graph to start fresh
    @param graph: EventKnowledgeGraph
    @param perf: Performance
    @return: None
    """

    print("Clearing DB...")
    graph.clear_db()
    perf.finished_step(log_message=f"Cleared DB")


def populate_graph(graph: EventKnowledgeGraph, perf: Performance):
    # region create EKG with event data and its context
    # import the events, location and activity records from all sublogs in the graph with the corresponding labels
    graph.import_data()
    perf.finished_step(log_message=f"(:Event), (:Location) and (:Activity) nodes done")

    # for each entity, we add the entity nodes to graph and correlate them (if possible) to the corresponding events
    graph.create_entities_by_nodes(node_label="Event")
    perf.finished_step(log_message=f"(:Entity) nodes done")

    graph.correlate_events_to_entities(node_label="Event")
    perf.finished_step(log_message=f"[:CORR] edges done")

    # create the classes
    graph.create_classes()
    perf.finished_step(log_message=f"(:Class) nodes done")

    # create [:IS]. [:PART_OF] and [:AT] relation
    graph.create_entity_relations_using_nodes()
    perf.finished_step(log_message=f"[:REL] edges done")
    # endregion

    # region Infer missing information
    # rule c, both for preceding load events and succeeding unload events
    graph.infer_items_propagate_upwards_multiple_levels(entity_type="Box", is_load=True)
    graph.infer_items_propagate_upwards_multiple_levels(entity_type="Box", is_load=False)
    graph.create_entity_relations_using_relations(relation_types=["AT_POS"])
    # rule d
    graph.infer_items_propagate_downwards_multiple_level_w_batching(entity_type="Box")
    # rule b
    graph.infer_items_propagate_downwards_one_level(entity_type="Box")

    # endregion

    # region Complete EKG creation, add DF relations after missing correlations are inferred
    graph.create_df_edges()
    perf.finished_step(log_message=f"[:DF] edges done")
    # endregion


def main() -> None:
    """
    Main function, read all the logs, clear and create the graph, perform checks
    @return: None
    """

    # performance class to measure performance
    perf = Performance(perf_path, number_of_steps=number_of_steps)
    graph = create_graph_instance(perf)

    if step_clear_db:
        clear_graph(graph=graph, perf=perf)

    if step_populate_graph:
        populate_graph(graph=graph, perf=perf)

    perf.finish()
    perf.save()

    graph.print_statistics()

    db_connection.close_connection()


if __name__ == "__main__":
    main()
