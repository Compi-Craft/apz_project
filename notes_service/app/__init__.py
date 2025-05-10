from fastapi import FastAPI
from app.get_services import register_service
from app import routes
import os

port = int(os.getenv("PORT", ""))
service_name = os.getenv("SERVICE_NAME", "")
register_service("notes_service", service_name, port)

app = FastAPI()

app.include_router(routes.router)
