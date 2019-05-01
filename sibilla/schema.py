from sibilla import DatabaseError, sql_identifier
from sibilla.caching import Cached, cachedmethod


# ---- Exceptions -------------------------------------------------------------


class SchemaError(DatabaseError):
    pass


# -----------------------------------------------------------------------------


class Schema(Cached):
    def __init__(self, db, schema):
        super().__init__()

        schema = sql_identifier(schema)

        self._user = db.fetch_one("""
            select *
            from   all_users
            where  username = :schema
        """,
        schema=schema)

        if not self._user:
            raise SchemaError(f"No such schema: {schema}")

        self._db = db

    @cachedmethod
    def __getattr__(self, name):
        return getattr(self._db, self._user.username + "." + name)

    @property
    def name(self):
        return self._user.username
