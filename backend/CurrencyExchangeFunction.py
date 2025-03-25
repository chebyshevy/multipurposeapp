import json
import logging
import boto3
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Secrets Manager client
secrets_manager_client = boto3.client('secretsmanager')

def get_api_key_from_secrets_manager(secret_name):
    try:
        # Retrieve the secret value from Secrets Manager
        response = secrets_manager_client.get_secret_value(SecretId=secret_name)
        # Secrets Manager returns the secret in a 'SecretString' field
        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
            return secret.get('apiKey')
        else:
            logging.error("Secret is in binary format, which is not expected.")
            return None
    except ClientError as e:
        logging.error(f"Error retrieving secret: {e}")
        return None

def lambda_handler(event, context):
    # Get the currency pair from the API request (if provided)
    base_currency = event.get('queryStringParameters', {}).get('base', 'USD')
    target_currency = event.get('queryStringParameters', {}).get('target', 'EUR')
    amount = event.get('queryStringParameters', {}).get('amount', 100)

    # Fetch the ExchangeRate-API key from Secrets Manager
    api_key = get_api_key_from_secrets_manager(secret_name='CurrencyExchangeApiKey')

    # Check if the API key exists
    if not api_key:
        logging.error("API key is missing")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'  # Allowing CORS for all origins
            },
            'body': json.dumps({'message': 'API key is missing'})
        }

    # Construct the API URL for the exchange rate
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'

    try:
        # Create the request object
        req = Request(url)

        # Send the request and get the response
        with urlopen(req) as response:
            # Read the response and decode it to a JSON format
            data = json.loads(response.read().decode())

            # Check if the response is successful
            if data['result'] == 'success':
                # Get the exchange rate for the target currency
                rate = data['conversion_rates'].get(target_currency)
                if rate:
                    converted_amount = rate * float(amount)
                    return {
                        'statusCode': 200,
                        'headers': {
                            'Access-Control-Allow-Origin': '*'  # Allowing CORS for all origins
                        },
                        'body': json.dumps({
                            'base': base_currency,
                            'target': target_currency,
                            'rate': rate,
                            'amount': amount,
                            'converted_amount': converted_amount
                        })
                    }
                else:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Access-Control-Allow-Origin': '*'  # Allowing CORS for all origins
                        },
                        'body': json.dumps({'message': 'Invalid target currency'})
                    }
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'  # Allowing CORS for all origins
                    },
                    'body': json.dumps({'message': 'Failed to fetch exchange rate data'})
                }

    except HTTPError as e:
        # Handle HTTP errors
        logging.error(f"HTTPError: {e.code} {e.reason}")
        return {
            'statusCode': e.code,
            'headers': {
                'Access-Control-Allow-Origin': '*'  # Allowing CORS for all origins
            },
            'body': json.dumps({'message': f'HTTP error: {e.reason}'})
        }
    except URLError as e:
        # Handle URL errors (e.g., network issues)
        logging.error(f"URLError: {e.reason}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'  # Allowing CORS for all origins
            },
            'body': json.dumps({'message': f'URL error: {e.reason}'})
        }
    except Exception as e:
        # Handle any other exceptions
        logging.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'  # Allowing CORS for all origins
            },
            'body': json.dumps({'message': f'Error: {str(e)}'})
        }
