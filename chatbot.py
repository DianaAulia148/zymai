import google.generativeai as genai

API_KEY = ""
genai.configure(api_key=API_KEY)

# Gunakan model yang dijamin tersedia
model = genai.GenerativeModel("models/gemini-2.5-flash")

def get_chatbot_response(user_message):
    try:
        response = model.generate_content(user_message)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
