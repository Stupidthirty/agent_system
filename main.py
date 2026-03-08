# main.py
from fastapi import FastAPI
from api.main import app

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Multi-Agent System...")
    print("API running at http://localhost:8000")
    print("Swagger docs at http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
