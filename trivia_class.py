import requests
import html
import os

available_trivia_databases = ['OpenTDB']
selected_trivia_database = 'OpenTDB'

def fetch_categories():
    if selected_trivia_database == 'OpenTDB':
        url = "https://opentdb.com/api_category.php"
        response = requests.get(url)
        categories = response.json()['trivia_categories']
        return categories
    
# Function to fetch questions from the API
def fetch_questions(amount=10, category=None, difficulty=None, qtype=None):
    if selected_trivia_database == 'OpenTDB':
        url = "https://opentdb.com/api.php"
    
        # Parameters for the request
        params = {
            "amount": amount,
            "category": category,
            "difficulty": difficulty,
            "type": qtype
        }
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v is not None}
        
        # Make the request to the API
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            if data["response_code"] == 0:
                return data['results']
            else:
                print("Error fetching questions.")
        else:
            print(f"Error connecting to the API: {response.status_code}")
        return []
    
