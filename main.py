from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .testing import testing
from . import customization

app = FastAPI()  

try:
    app.include_router(testing.router, prefix="/testing")
except FileNotFoundError as e:
    print("The 'testing' dir is missing and will not load")
except Exception as e:
    print(f"An error occurred while loading the 'testing' blueprint: {e}")