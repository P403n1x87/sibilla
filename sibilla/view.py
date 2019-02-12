from .table import Table

class View(Table):
    __table__ = None

    def __repr__(self):
        return "<view '{}'>".format(self.name.upper())
