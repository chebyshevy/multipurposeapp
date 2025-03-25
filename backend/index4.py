import json
import logging
import os
import boto3
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote  # Import urllib.parse.quote for URL encoding

# Define the logger at the beginning of your code
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a Secrets Manager client
secrets_client = boto3.client('secretsmanager')

def get_secret_value(secret_name):
    try:
        # Retrieve the secret value from Secrets Manager
        response = secrets_client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            # Return the secret value as a string (JSON format)
            return json.loads(response['SecretString'])
        else:
            # If the secret is binary, decode and return
            return json.loads(response['SecretBinary'])
    except Exception as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise e

def lambda_handler(event, context):
    # Fetch the secret value from Secrets Manager
    secret_name = os.getenv('SECRET_NAME')  # This should be passed as an environment variable (e.g., AccuWeatherAPIKeySecret)
    if not secret_name:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',  # Allow all origins for testing, restrict in production
                'Access-Control-Allow-Methods': 'GET, OPTIONS',  # Allow GET and OPTIONS methods
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',  # Allow necessary headers
            },
            'body': json.dumps({'error': 'Secret name is missing.'})
        }

    try:
        secrets = get_secret_value(secret_name)
        API_KEY = secrets.get('API_KEY')  # Assuming the secret JSON has a field "API_KEY"
        
        if not API_KEY:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*', 
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',  
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
                'body': json.dumps({'error': 'API key is missing in the secret.'})
            }

        logger.info(f"Using API Key: {API_KEY}")  # Log the API key for debugging (remove in production)

        BASE_URL = 'https://dataservice.accuweather.com/'

        # Safely access queryStringParameters or pathParameters with default values
        city = 'New York'  # Default city
        if event.get('queryStringParameters') and 'city' in event['queryStringParameters']:
            city = event['queryStringParameters']['city']
        elif event.get('pathParameters') and 'city' in event['pathParameters']:
            city = event['pathParameters']['city']

        # URL-encode the city name
        encoded_city = quote(city)
        
        # Step 1: Get location key
        location_url = f"{BASE_URL}locations/v1/cities/search"
        location_params = f'?apikey={API_KEY}&q={encoded_city}'
        
        try:
            location_request = Request(location_url + location_params)
            location_response = urlopen(location_request)
            location_data = json.load(location_response)
            
            if not location_data:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    },
                    'body': json.dumps({'error': 'City not found.'})
                }
            
            location_key = location_data[0]['Key']
            
            # Step 2: Get current conditions
            conditions_url = f"{BASE_URL}currentconditions/v1/{location_key}"
            conditions_params = f'?apikey={API_KEY}'
            
            conditions_request = Request(conditions_url + conditions_params)
            conditions_response = urlopen(conditions_request)
            conditions_data = json.load(conditions_response)
            
            # Extract relevant data from conditions_data safely
            conditions = conditions_data[0] if conditions_data else {}
            
            temperature = conditions.get('Temperature', {}).get('Metric', {}).get('Value', None)
            weather = conditions.get('WeatherText', 'Unknown weather')
            city = city

            if temperature is None:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    },
                    'body': json.dumps({'error': 'Temperature data not found.'})
                }

            relevant_data = {
                'temperature': temperature,
                'weather': weather,
                'city': city
            }

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
                'body': json.dumps(relevant_data)
            }
            
        except HTTPError as e:
            logger.error(f"HTTP Error occurred: {str(e)}")
            return {
                'statusCode': e.code,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
                'body': json.dumps({'error': f"HTTP Error: {str(e)}"})
            }
        except URLError as e:
            logger.error(f"URL Error occurred: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
                'body': json.dumps({'error': f"URL Error: {str(e)}"})
            }
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
                'body': json.dumps({'error': f"Unexpected error: {str(e)}"})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            },
            'body': json.dumps({'error': f"Failed to retrieve the secret: {str(e)}"})
        }
