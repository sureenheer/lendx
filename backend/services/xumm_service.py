"""
Xumm Wallet Service
Server-side proxy for Xumm SDK operations to avoid CORS issues
"""

import os
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from root .env.local file
env_path = Path(__file__).resolve().parent.parent.parent / '.env.local'
load_dotenv(dotenv_path=env_path)

# Xumm API configuration
XUMM_API_KEY = os.getenv('NEXT_PUBLIC_XUMM_API_KEY', '').strip('"')
XUMM_API_SECRET = os.getenv('NEXT_PUBLIC_XUMM_API_SECRET', '').strip('"')
XUMM_API_BASE = 'https://xumm.app/api/v1/platform'


class XummService:
    """Service for interacting with Xumm API"""
    
    def __init__(self):
        if not XUMM_API_KEY or not XUMM_API_SECRET:
            raise ValueError("Xumm API credentials not configured")
        
        self.api_key = XUMM_API_KEY
        self.api_secret = XUMM_API_SECRET
        self.headers = {
            'X-API-Key': self.api_key,
            'X-API-Secret': self.api_secret,
            'Content-Type': 'application/json'
        }
    
    async def create_signin_payload(self) -> Dict[str, Any]:
        """
        Create a sign-in payload for wallet connection
        Returns payload UUID and QR code URL
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{XUMM_API_BASE}/payload',
                headers=self.headers,
                json={
                    'txjson': {
                        'TransactionType': 'SignIn'
                    }
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create Xumm payload: {response.text}")
            
            data = response.json()
            return {
                'uuid': data['uuid'],
                'qr_url': data['refs']['qr_png'],
                'deeplink': data['next']['always'],
                'websocket_url': data['refs']['websocket_status']
            }
    
    async def create_transaction_payload(self, tx_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a transaction payload for signing
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{XUMM_API_BASE}/payload',
                headers=self.headers,
                json={'txjson': tx_json},
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create Xumm payload: {response.text}")
            
            data = response.json()
            return {
                'uuid': data['uuid'],
                'qr_url': data['refs']['qr_png'],
                'deeplink': data['next']['always'],
                'websocket_url': data['refs']['websocket_status']
            }
    
    async def get_payload_status(self, payload_uuid: str) -> Dict[str, Any]:
        """
        Get the status of a payload
        Returns signed status and account address if signed
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{XUMM_API_BASE}/payload/{payload_uuid}',
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get payload status: {response.text}")
            
            data = response.json()
            meta = data.get('meta', {})
            response_data = data.get('response', {})
            
            return {
                'signed': meta.get('signed', False),
                'cancelled': meta.get('cancelled', False),
                'expired': meta.get('expired', False),
                'account': response_data.get('account'),
                'txid': response_data.get('txid')
            }
    
    async def cancel_payload(self, payload_uuid: str) -> bool:
        """Cancel a pending payload"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f'{XUMM_API_BASE}/payload/{payload_uuid}',
                headers=self.headers,
                timeout=30.0
            )
            
            return response.status_code == 200


# Singleton instance
_xumm_service: Optional[XummService] = None


def get_xumm_service() -> XummService:
    """Get or create Xumm service instance"""
    global _xumm_service
    if _xumm_service is None:
        _xumm_service = XummService()
    return _xumm_service
