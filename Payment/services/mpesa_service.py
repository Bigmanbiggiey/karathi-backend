import requests
import base64
from datetime import datetime
from django.conf import settings


class MPesaService:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        
        if settings.MPESA_ENVIRONMENT == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """Get OAuth access token"""
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_base64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_base64}'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()['access_token']
    
    def generate_password(self):
        """Generate password for STK push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(data_to_encode.encode()).decode('utf-8')
        return password, timestamp
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push"""
        access_token = self.get_access_token()
        password, timestamp = self.generate_password()
        
        # Format phone number (remove leading 0, add 254)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        print(f"Callback URL being sent: {self.callback_url}")
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": 'KARATHI GREENSCAPE',
            "TransactionDesc": transaction_desc
        }
        
        print(f"Full payload: {payload}")

        response = requests.post(url, json=payload, headers=headers)
        return response.json()