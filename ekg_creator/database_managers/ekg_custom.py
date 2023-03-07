from typing import List, Set, Optional, Dict

from database_managers.db_connection import DatabaseConnection
from utilities.performance_handling import Performance
from database_managers.custom_query_library import CustomCypherQueryLibrary as ccql


class EKGCustom:
    def __init__(self, db_connection: DatabaseConnection, perf: Performance):
        self.connection = db_connection
        self.perf = perf

    def _write_message_to_performance(self, message: str):
        if self.perf is not None:
            self.perf.finished_step(activity=message)

    def create_location_nodes(self):
        self.connection.exec_query(ccql.get_create_location_nodes_query)
        self.connection.exec_query(ccql.get_create_part_of_relation_location_nodes_query)
        self.connection.exec_query(ccql.get_create_at_relation_between_events_and_locations_query)
