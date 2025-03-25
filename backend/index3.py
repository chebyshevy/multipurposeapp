import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def lambda_handler(event, context):
    # Open Trivia Database API URL
    api_url = "https://opentdb.com/api.php"
    
    # Fetch category and difficulty from the event (query parameters)
    category = event.get('queryStringParameters', {}).get('category', 9)  # Default to General Knowledge (ID: 9)
    difficulty = event.get('queryStringParameters', {}).get('difficulty', 'easy')  # Default to easy
    
    # Number of questions to fetch
    amount = 5  # Default to 5 questions
    
    # Parameters to pass to the API (Category and Difficulty are dynamic now)
    params = {
        'amount': amount,  # Number of questions to pull
        'type': 'multiple',  # Type of questions (multiple choice)
        'category': category,  # Category from query parameter
        'difficulty': difficulty  # Difficulty from query parameter
    }
    
    # URL encode the parameters
    query_string = urlencode(params)
    full_url = f"{api_url}?{query_string}"
    
    # Make a request to the Open Trivia Database API
    req = Request(full_url)
    try:
        with urlopen(req) as response:
            # If the response is successful, read and parse the response body
            data = json.loads(response.read().decode())
        
        # Extract the questions and format them for the API response
        questions = []
        for question in data['results']:
            questions.append({
                'question': question['question'],
                'correct_answer': question['correct_answer'],
                'incorrect_answers': question['incorrect_answers'],
            })
        
        # Return the questions along with the Access-Control-Allow-Origin header
        return {
            'statusCode': 200,
            'body': json.dumps(questions),
            'headers': {
                'Access-Control-Allow-Origin': '*',  # Allow all origins to access the resource
                'Content-Type': 'application/json'
            }
        }
    except Exception as e:
        # If the API request fails, return an error message with the Access-Control-Allow-Origin header
        return {
            'statusCode': 500,
            'body': json.dumps({"error": f"Unable to fetch questions from the trivia API: {str(e)}"}),
            'headers': {
                'Access-Control-Allow-Origin': '*',  # Allow all origins to access the resource
                'Content-Type': 'application/json'
            }
        }
