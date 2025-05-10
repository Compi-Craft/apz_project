from fastapi import FastAPI
from app import routes
from app.database import engine
from app.models import Base
from app.get_redis import register_service
import os

Base.metadata.create_all(bind=engine)

port = int(os.getenv("PORT", ""))
service_name = os.getenv("SERVICE_NAME", "")
register_service("auth_service", service_name, port)

app = FastAPI()


app.include_router(routes.router)
