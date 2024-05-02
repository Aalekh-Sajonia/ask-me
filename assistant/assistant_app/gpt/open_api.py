from openai import OpenAI
import os

key =  PHOENIX_WS_HOST = os.getenv("OPEN_AI_KEY", "") 
client = OpenAI(api_key=key)