from dotenv import load_dotenv
load_dotenv()
import os
import google.generativeai as genai
genai.configure(api_key=("AIzaSyDM9xdKD9JDW_wu6Lp1gnCraUK3Ds-DPNc"))
#GOOGLE_API_KEY = "AIzaSyDM9xdKD9JDW_wu6Lp1gnCraUK3Ds-DPNc"


prompt = """
You are an automatic email extractor. You need to extract the body part from the email then you have to
summarize it. Remove all the relevant parts of the mail.
Just contain the text part in the summary. Not any unnecessary header like summary or body something. Just provide text.
"""

def generate_message(query):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + query)
    response_count = model.generate_content(prompt + query)
    print(response_count)
    return response.text

def token_count(query):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + query)
    return response.usage_metadata.total_token_count