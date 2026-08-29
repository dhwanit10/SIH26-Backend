from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.test import createTables
from app.core.init_db import init_database, reset_database
from sqlalchemy import text
# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# uncomment this for the first time and then remove this code. 
# createTables()


# Include routers
# app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
# app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
# app.include_router(verification.router, prefix=f"{settings.API_V1_STR}/verification", tags=["verification"])
from app.api.v1.endpoints import workflow, history, documents, system, session, auth
app.include_router(workflow.router, prefix=f"{settings.API_V1_STR}/workflow", tags=["workflow"])
app.include_router(history.router, prefix=f"{settings.API_V1_STR}/data", tags=["data"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
app.include_router(system.router, prefix=f"{settings.API_V1_STR}/system", tags=["system"])
app.include_router(session.router, prefix=f"{settings.API_V1_STR}/session", tags=["session"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])


@app.get("/")
async def root():
    # try:
    #     with engine.connect() as conn:
    #         result = conn.execute(text("SELECT 1"))
    #         print("✅ Database connection successful!")
    # except Exception as e:
    #     print(f"❌ Database connection failed: {e}")
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}