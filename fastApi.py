#!/usr/bin/env python3
"""
Simple FastAPI Server - Weather Route Only
"""

from fastapi import FastAPI, HTTPException, Header, Query
from typing import Optional
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Get wallet address from environment or use default
RECIPIENT_WALLET = os.getenv("RECIPIENT_WALLET", "0x9953a068639e409133baAcdd4513D9637D20132f")
PAYMENT_AMOUNT = os.getenv("PAYMENT_AMOUNT", "0.00000001")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

def get_weather_data(location: str) -> dict:
    """
    Get current weather for a location using WeatherAPI.com
    
    Args:
        location (str): Location (city name, coordinates, zip code, etc.)
        
    Returns:
        dict: Weather data from the API
    """
    if not WEATHER_API_KEY:
        return {"error": "WEATHER_API_KEY not found in environment variables"}
    
    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        'key': WEATHER_API_KEY,
        'q': location
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}

@app.get("/weather")
async def get_weather(
    payment_tx_hash: Optional[str] = Header(None, alias="payment-tx-hash"),
    location: str = Query(default="London", description="Location to get weather for")
):
    """Get weather data - requires ETH payment"""
    
    print(f"[API] Weather request for location: {location}")
    print(f"[API] Payment hash: {'provided' if payment_tx_hash else 'required'}")
    
    if not payment_tx_hash:
        # Return 402 Payment Required
        raise HTTPException(
            status_code=402,
            detail="Payment required",
            headers={
                "x402-amount": PAYMENT_AMOUNT,
                "x402-recipient": RECIPIENT_WALLET,
                "x402-currency": "ETH"
            }
        )
    
    # Get real weather data
    print(f"[API] Fetching weather data for: {location}")
    weather_data = get_weather_data(location)
    print(f"[API] Weather data retrieved successfully")
    
    # Add payment information to response
    weather_data["payment_info"] = {
        "paid_with": payment_tx_hash,
        "payment_amount": PAYMENT_AMOUNT,
        "timestamp": time.time(),
        "requested_location": location
    }
    
    return weather_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4021)