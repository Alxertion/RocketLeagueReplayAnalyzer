from src.query import Query
from tkinter import INSERT, END


class QueryManager:
    def __init__(self, main_frame):
        self.main_frame = main_frame
        self.queries = []

    def add_query(self, query: Query):
        self.queries.append(query)

    def add_message(self, message: dict):
        for query in self.queries:
            result = query.add_message(message)
            if result is not None:
                self.main_frame.query_output.config(state="normal")
                self.main_frame.query_output.insert(INSERT, result + "\n")
                self.main_frame.query_output.config(state="disabled")
