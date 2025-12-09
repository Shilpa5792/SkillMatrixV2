from fastapi import FastAPI
from skill_hierarchy_service2 import skill_hierarchy_complete_service
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API is running"}

@app.get("/api/hierarchy/complete")
def get_complete_hierarchy():
    result = skill_hierarchy_complete_service.get_complete_hierarchy_optimized()
    return result

if __name__ == "__main__":
    print("API running at: http://localhost:8000/api/hierarchy/complete")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)