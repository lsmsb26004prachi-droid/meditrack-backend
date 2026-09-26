from database import Base, engine
import models  # noqa: F401  (loading this registers the tables)

Base.metadata.create_all(engine)
print("Tables created")