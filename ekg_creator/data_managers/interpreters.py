from data_managers.query_translators import ClassCypher, ConditionCypher, EntityCypher


class Interpreter:
    def __init__(self, query_language):
        self.class_query_interpreter = None
        self.condition_query_interpreter = None
        self.entity_query_interpreter = None
        self.set_interpreters(query_language)

    def set_interpreters(self, query_language):
        if query_language == "Cypher":
            self.class_query_interpreter = ClassCypher
            self.condition_query_interpreter = ConditionCypher
            self.entity_query_interpreter = EntityCypher
