import requests
from django.conf import settings


class AirtelMoneyService:
    def __init__(self):
        self.client_id = settings.AIRTEL_CLIENT_ID
        self.client_secret = settings.AIRTEL_CLIENT_SECRET
        self.api_key = settings.AIRTEL_API_KEY
        
        if settings.AIRTEL_ENV == 'production':
            self.base_url = 'https://openapiuat.airtel.africa'
        else:
            self.base_url = 'https://openapiuat.airtel.africa'  # staging
    
    def get_access_token(self):
        """Get OAuth access token"""
        url = f"{self.base_url}/auth/oauth2/token"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()['access_token']
    
    def initiate_payment(self, phone_number, amount, reference, transaction_id):
        """Initiate Airtel Money payment"""
        access_token = self.get_access_token()
        
        # Format phone number for Airtel (country code without +)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        url = f"{self.base_url}/merchant/v1/payments/"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Country': 'KE',
            'X-Currency': 'KES'
        }
        
        payload = {
            "reference": reference,
            "subscriber": {
                "country": "KE",
                "currency": "KES",
                "msisdn": phone_number
            },
            "transaction": {
                "amount": float(amount),
                "country": "KE",
                "currency": "KES",
                "id": transaction_id
            }
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()