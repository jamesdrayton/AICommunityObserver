from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from . import testing
    from . import customization
except ImportError as e:
    print("Missing directories to run the API for customization and/or testing.")
except Exception as e:
    raise e

app = FastAPI()  

try:
    app.include_router(testing.router, prefix="/testing")
except FileNotFoundError as e:
    print("The 'testing' dir is missing and will not load")
except Exception as e:
    print(f"An error occurred while loading the 'testing' blueprint: {e}")

try: 
    app.include_router(customization.customization_router, prefix="/customization")
except FileNotFoundError as e:
    print("The 'customization' dir is missing and will not load")
except Exception as e:
    print(f"An error occurred while loading the 'customization' blueprint: {e}")