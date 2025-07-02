import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class Assistant:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4o"

    def send(self, message: str, previous_response_id: str = None):
        params = {
            "model": self.model,
            "input": message,
        }
        if previous_response_id:
            params["previous_response_id"] = previous_response_id

        try:
            resp = self.client.responses.create(**params)
            print("📨 [Full API response]:", resp)
            text = (
                resp.output[0].content[0].text
                if isinstance(resp.output[0].content[0].text, str)
                else resp.output[0].content[0].text.value
            )
            return {
                "id": resp.id,
                "text": text,
            }
        except Exception as e:
            return {
                "id": None,
                "text": f"⚠️ Error: {str(e)}",
            }
