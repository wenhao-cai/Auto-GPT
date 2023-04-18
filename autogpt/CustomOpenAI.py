import requests
import uuid


class CustomOpenAI:
    def __init__(self, api_base_url, token_name=None):
        self.api_base_url = api_base_url
        self.token_name = token_name
        self.headers = {
            "Content-Type": "application/json",
        }

    def _build_url(self, path):
        url = f"{self.api_base_url}{path}"
        if self.token_name:
            url += f"?token={self.token_name}"
        return url

    def list_models(self):
        response = requests.get(self._build_url("/api/models"), headers=self.headers)
        return response.json()

    def list_conversations(self, offset=1, limit=20):
        params = {"offset": offset, "limit": limit}
        response = requests.get(self._build_url("/api/conversations"), params=params, headers=self.headers)
        return response.json()

    def delete_all_conversations(self):
        response = requests.delete(self._build_url("/api/conversations"), headers=self.headers)
        return response.json()

    def get_conversation(self, conversation_id):
        response = requests.get(self._build_url(f"/api/conversation/{conversation_id}"), headers=self.headers)
        return response.json()

    def delete_conversation(self, conversation_id):
        response = requests.delete(self._build_url(f"/api/conversation/{conversation_id}"), headers=self.headers)
        return response.json()

    def update_conversation_title(self, conversation_id, title):
        data = {"title": title}
        response = requests.patch(self._build_url(f"/api/conversation/{conversation_id}"), json=data, headers=self.headers)
        return response.json()

    def generate_conversation_title(self, conversation_id, model, message_id):
        data = {"model": model, "message_id": message_id}
        response = requests.post(self._build_url(f"/api/conversation/gen_title/{conversation_id}"), json=data, headers=self.headers)
        return response.json()

    def talk(self, prompt, model, message_id=None, parent_message_id=None, conversation_id=None, stream=False):
        if message_id is None:
            message_id = str(uuid.uuid4())
        if parent_message_id is None:
            parent_message_id = str(uuid.uuid4())

        data = {
            "prompt": prompt,
            "model": model,
            "message_id": message_id,
            "parent_message_id": parent_message_id,
            "conversation_id": conversation_id,
            "stream": stream
        }
        response = requests.post(self._build_url("/api/conversation/talk"), json=data, headers=self.headers)
        return response.json()

    def regenerate(self, prompt, model, message_id, parent_message_id, conversation_id, stream=False):
        data = {
            "prompt": prompt,
            "model": model,
            "message_id": message_id,
            "parent_message_id": parent_message_id,
            "conversation_id": conversation_id,
            "stream": stream
        }
        response = requests.post(self._build_url("/api/conversation/regenerate"), json=data, headers=self.headers)
        return response.json()

    def go_on(self, model, parent_message_id, conversation_id, stream=False):
        data = {
            "model": model,
            "parent_message_id": parent_message_id,
            "conversation_id": conversation_id,
            "stream": stream
            }
        response = requests.post(self._build_url("/api/conversation/goon"), json=data, headers=self.headers)
        return response.json()