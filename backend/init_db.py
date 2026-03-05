from .db import engine, Base
from . import models   # <-- THIS is the missing line!

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
