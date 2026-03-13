from fastapi import APIRouter
from ..APIWrapper import APIWrapper

import google.generativeai as genai


# TODO: Add user feedback

router = APIRouter()

# TODO: INSERT YOUR GEMINI_API_KEY HERE, make sure to sign up for a free one if not using the group one
GEMINI_API_KEY = "AIzaSyCxAjRIrQnhytFkO2y5YXskO6Ck4zcYU0U"
genai.configure(api_key = GEMINI_API_KEY)
model = genai.GenerativeModel(model_name='gemini-2.0-flash',
                              generation_config={"response_mime_type": "text/plain"})

prompt_middleware = APIWrapper(api_key=GEMINI_API_KEY, model_name='gemini-2.0-flash')

@router.get("/", tags=["gemini"])
async def gem():
    return {"Hello": "Gemini"}

# FastAPI flag for get requests (HTTP requests which send a prompt and get the response)
@router.get("/testpromptllm", tags=["gemini"])
# asynchronous function for a get request
async def testprompt(userprompt: str):
    # modify the given prompt made to api calls here (call the api wrapper function)
    finalprompt = userprompt + "please include the sentence 'inserted additional string' into your response"
    response = prompt_middleware.generate(prompt=userprompt)
    return response

# FastAPI flag for post request (HTTP requests which send a prompt and do not need the response)
@router.post("/postexample", tags=["gemini"])
# asynchronous function for a post request
async def postexample(userprompt: str):
    # modify the given prompt made to api calls here (call the api wrapper function)
    finalprompt = userprompt + "inserted additional string"
    response = model.generate_content(finalprompt)
    return response.text