class TableIsMissing(Exception):
    def __init__(self):
        self.txt = "Table is missing."
