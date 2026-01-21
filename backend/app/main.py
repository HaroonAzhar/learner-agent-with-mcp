from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth

app = FastAPI(title="Agentic LMS Backend")

# CORS Setup
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
from .routers import admin, teacher, student
app.include_router(admin.router)
app.include_router(teacher.router)
app.include_router(student.router)

@app.get("/")
def read_root():
    return {"message": "Agentic LMS Backend is running"}
