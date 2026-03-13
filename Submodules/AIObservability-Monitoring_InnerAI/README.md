# AIObservability-Monitoring_InnerAI


Project Name: **AI Observability & Monitoring**

Group Name: **Inner AI**

Main Participant Name: **James Drayton Beninger**

Team Participant Names:

Amogh Thoutu, Farhan Mahamud, Shubhangi Singh, Bardia Azami

Purpose: Create a middleware solution which can integrate into target audience apps (requiring developer access)

Audience: Text-based GenAI applications. Anything that includes sending a text prompt to an LLM and which receives text back (can reduce scope if this is too much)

This application is designed to act as middleware between calls to an LLM from a GenAI application and the actual LLM being used by the application. It will do this by replacing the python function calls which prompt the LLM for a response and wrapping that function call in additional monitoring and testing code. It's composed of 4 modules: an APIWrapper, metrics, dashboard, and testing (a simulated end user)

------------------------------------------------------- -

AWS Codes:

James Drayton Beninger: XXXXXXXXXXX 

Amogh Thoutu: XXXXXXXXXXX 

Farhan Mahamud : XXXXXXXXXXX 

Shubhangi Singh : XXXXXXXXXXX 

Bardia Azami : XXXXXXXXXXX 

Link to Design Document: <br>
https://docs.google.com/document/d/11zHLGLNiTjiFe3ZNxA3lkbRvfso0iWw7NkKMGZmBAxE/edit?tab=t.0 <br>

Packages: <br>
conda install conda-forge::fastapi <br>
conda install conda-forge::langchain <br>
conda install anaconda::prometheus_client <br>
ftpdf <br>
google.generativeai <br> 
weasyprint <br>

To run use command "fastapi dev main.py" <br>
Access at http://127.0.0.1:8000/docs <br>
