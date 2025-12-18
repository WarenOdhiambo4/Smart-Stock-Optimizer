import requests
import os
from django.conf import settings

class AirtableWebhookManager:
    def __init__(self):
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.token = os.getenv('AIRTABLE_API_KEY')
        self.base_url = f"https://api.airtable.com/v0/bases/{self.base_id}"
    
    def register_webhook(self, notify_url):
        """Register webhook with Airtable - run once"""
        url = f"{self.base_url}/webhooks"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {
            "notificationUrl": notify_url,
            "specification": {
                "options": {
                    "filters": {
                        "dataTypes": ["tableData"]
                    }
                }
            }
        }
        response = requests.post(url, headers=headers, json=data)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        return response.json()
    
    def get_payload(self, webhook_id, cursor=None):
        """Get actual payload data from Airtable"""
        url = f"{self.base_url}/webhooks/{webhook_id}/payloads"
        if cursor:
            url += f"?cursor={cursor}"
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        return response.json()
    
    def refresh_webhook(self, webhook_id):
        """Refresh webhook to prevent expiry"""
        url = f"{self.base_url}/webhooks/{webhook_id}/refresh"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(url, headers=headers)
        return response.json()