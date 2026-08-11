from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .testing import testing
    from . import customization
except Exception as e:
    print("Missing directories to run the API for customization and/or testing")

app = FastAPI()  

try:
    app.include_router(testing.router, prefix="/testing")
except FileNotFoundError as e:
    print("The 'testing' dir is missing and will not load")
except Exception as e:
    print(f"An error occurred while loading the 'testing' blueprint: {e}")