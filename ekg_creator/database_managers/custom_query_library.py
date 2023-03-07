from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class Query:
    query_string: str
    kwargs: Optional[Dict[str, any]]


class CustomCypherQueryLibrary:

    @staticmethod
    def get_create_location_nodes_query():
        query = '''
            MATCH (lt:LocationType)
            MATCH (eq:Equipment)
            WHERE eq.ID in lt.equipment
            MERGE (l:Location {ID: eq.ID + lt.ID, uID: 'Location' + eq.ID + lt.ID})
            MERGE (l) - [:IS] -> (lt)
            MERGE (l) - [:OF] -> (eq)
            RETURN l, lt, eq
        '''

        return Query(query_string=query, kwargs={})

    @staticmethod
    def get_create_part_of_relation_location_nodes_query():
        query = '''
            MATCH (l1:Location) - [:OF] -> (:Equipment) <- [:OF] - (l2:Location)
            WHERE l1 <> l2
            MATCH (l1) - [:IS] -> (:LocationType) - [:PART_OF] -> (:LocationType) <- [:IS] - (l2)
            MERGE (l1) - [:PART_OF] -> (l2)
        '''

        return Query(query_string=query, kwargs={})

    @staticmethod
    def get_create_at_relation_between_events_and_locations_query():
        query = '''
            MATCH (l:Location) - [:OF] -> (:Equipment) <- [:CORR] - (e:Event)
            MATCH (e) - [:OBSERVED] -> (:Class) <- [:AT] - (:LocationType) <- [:IS] - (l)
            MERGE (e) - [:AT] -> (l)
            
        '''

        return Query(query_string=query, kwargs={})