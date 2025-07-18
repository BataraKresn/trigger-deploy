from sqlalchemy import create_engine, MetaData

DATABASE_URL = "postgresql://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Example table definition
# from sqlalchemy import Table, Column, Integer, String
# users = Table(
#     "users",
#     metadata,
#     Column("id", Integer, primary_key=True),
#     Column("username", String, unique=True),
#     Column("password", String)
# )

metadata.create_all(engine)
