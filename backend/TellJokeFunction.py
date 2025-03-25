import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def lambda_handler(event, context):
    # URL of JokeAPI
    url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,racist,sexist,explicit"
    
    try:
        # Making the request to JokeAPI
        req = Request(url)
        with urlopen(req) as response:
            joke_data = json.load(response)

        # Constructing the response based on the JokeAPI response
        if 'joke' in joke_data:
            joke = joke_data['joke']
        else:
            joke = f"{joke_data['setup']} - {joke_data['delivery']}"

        # Prepare the response with CORS headers
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Allow all origins for CORS
            },
            'body': json.dumps({
                'joke': joke
            })
        }
    
    except HTTPError as e:
        # Handle error from JokeAPI
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'HTTP error occurred: {str(e)}'
            })
        }
    
    except URLError as e:
        # Handle URL error
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'URL error occurred: {str(e)}'
            })
        }
    
    except Exception as e:
        # Handle any other errors
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'An error occurred: {str(e)}'
            })
        }
