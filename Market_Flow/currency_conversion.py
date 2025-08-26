import requests
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_KEY = os.getenv('API_KEY')
BASE_CURRENCY = 'USD'
TARGET_CURRENCY = 'EGP'
FALLBACK_RATE = 47.5  # Fallback rate in case the API fails

def get_usd_to_egp_rate():
    """
    Fetches the latest USD to EGP exchange rate from an API.
    Returns a fallback rate if the API call fails or no API key is provided.
    """
    if not API_KEY:
        print("INFO: API_KEY not found. Using fallback exchange rate.")
        return FALLBACK_RATE

    url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{BASE_CURRENCY}'
    try:
        response = requests.get(url, timeout=5) # Add a timeout
        response.raise_for_status()
        data = response.json()
        if data.get('result') == 'success':
            rate = data['conversion_rates'][TARGET_CURRENCY]
            print(f"Successfully fetched exchange rate: 1 USD = {rate} EGP")
            return rate
        else:
            print(f"API Error: {data.get('error-type')}. Using fallback rate.")
            return FALLBACK_RATE
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch exchange rate: {e}. Using fallback rate.")
        return FALLBACK_RATE

if __name__ == "__main__":
    # Example of how to use the function
    rate = get_usd_to_egp_rate()
    print(f"The current or fallback USD to EGP rate is: {rate}")
