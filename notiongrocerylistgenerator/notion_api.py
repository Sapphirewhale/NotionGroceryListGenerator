import json
import requests


class NotionApi:
    def __init__(self, token) -> None:
        self.token = token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2021-08-16",
            "Content-Type": "application/json",
        }

    def _get(self, uri):
        r = requests.get(
            uri,
            headers=self._headers(),
        )
        if r.status_code >= requests.codes.bad_request:
            print("An error occurred:")
            print(r.json())
        return r.json()

    def _post(self, uri, data={}):
        r = requests.post(uri, headers=self._headers(), data=json.dumps(data))

        if r.status_code >= requests.codes.bad_request:
            print("An error occurred:")
            print(r.json())
        return r.json()

    def get_page(self, id):
        return self._get(f"https://api.notion.com/v1/pages/{id}")

    def get_database(self, id):
        return self._get(f"https://api.notion.com/v1/databases/{id}")

    def get_blocks(self, id):
        return self._get(f"https://api.notion.com/v1/blocks/{id}/children")

    def query(self, id):
        return self._post(f"https://api.notion.com/v1/databases/{id}/query")

    def create_page(self, payload):
        return self._post("https://api.notion.com/v1/pages", payload)
