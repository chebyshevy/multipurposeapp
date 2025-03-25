import json
import boto3
import os
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from datetime import datetime

# DynamoDB client
dynamo_db = boto3.client('dynamodb')

# Secrets Manager client
secrets_manager = boto3.client('secretsmanager')

def get_news_api_key():
    secret_name = "NewsAPIKey"  # Hardcoded secret name
    
    try:
        # Fetch the secret value from AWS Secrets Manager
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        
        # Secrets Manager may return either 'SecretString' or 'SecretBinary'
        secret = response.get('SecretString')
        
        if secret:
            secret_dict = json.loads(secret)
            return secret_dict.get('api_key')  # Assuming the secret has the structure {'api_key': 'your-api-key'}
        else:
            raise ValueError("No SecretString found in response")
    
    except Exception as e:
        print(f"Error fetching secret: {e}")
        raise e

def lambda_handler(event, context):
    # Fetch the NewsAPI Key from Secrets Manager directly
    NEWS_API_KEY = get_news_api_key()

    if not NEWS_API_KEY:
        raise ValueError("API key could not be retrieved from Secrets Manager")

    # API endpoint for top headlines
    url = 'https://newsapi.org/v2/top-headlines'
    
    # Query parameters for the API request
    params = {
        'apiKey': NEWS_API_KEY,
        'country': 'us',  # You can change this to your preferred country
        'category': 'general',  # You can change this to another category
    }

    # Encode the parameters
    query_string = urlencode(params)
    full_url = f"{url}?{query_string}"

    try:
        # Create a request object
        request = Request(full_url)
        
        # Fetch data from NewsAPI using urlopen
        with urlopen(request) as response:
            news_data = json.load(response)

        if news_data.get('status') == 'ok':
            # Process each article
            for article in news_data['articles']:
                article_item = {
                    'id': {'S': article['url']},
                    'title': {'S': article['title']},
                    'description': {'S': article.get('description', '') or ''},
                    'publishedAt': {'S': article['publishedAt']},
                    'url': {'S': article['url']}
                }
                
                # Insert each article into DynamoDB
                dynamo_db.put_item(
                    TableName='NewsArticles',
                    Item=article_item
                )
            
            return {
                'statusCode': 200,
                'body': json.dumps(news_data),
                'headers': {
                    'Access-Control-Allow-Origin': '*',  # Allow all origins
                    'Content-Type': 'application/json'
                }
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Failed to fetch news'}),
                'headers': {
                    'Access-Control-Allow-Origin': '*',  # Allow all origins
                    'Content-Type': 'application/json'
                }
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)}),
            'headers': {
                'Access-Control-Allow-Origin': '*',  # Allow all origins
                'Content-Type': 'application/json'
            }
        }
