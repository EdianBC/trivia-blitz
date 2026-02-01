import requests
import html
import aiohttp
import asyncio

available_trivia_databases = ['OpenTDB']

#region Fetch Cat Async
async def fetch_categories_async(trivia_database="OpenTDB"):
    if trivia_database == 'OpenTDB':
        return await fetch_categories_opentdb()
                

async def fetch_categories_opentdb():
    url = "https://opentdb.com/api_category.php"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                categories = data['trivia_categories']
                return categories
            else:
                print(f"Error connecting to the API: {response.status}")
                return []




#region Fetch Qs Async

# Must return list of dictionaries with keys: 'question':str, 'correct_answer':str, 'incorrect_answers':list[str]
async def fetch_questions_async(trivia_database="OpenTDB", amount=10, category=None, difficulty=None, qtype=None):
    if trivia_database == 'OpenTDB':
        return await fetch_questions_opentdb(amount, category, difficulty, qtype)


async def fetch_questions_opentdb(amount=10, category=None, difficulty=None, qtype=None):
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
    
    questions = []
    # Make the request to the API
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["response_code"] == 0:
                    questions = data['results']
                else:
                    print("Error fetching questions.")
                    return []
            else:
                print(f"Error connecting to the API: {response.status}")
                return []
    
    #Eliminate all keys except 'question', 'correct_answer', 'incorrect_answers'
    questions = [{'question': html.unescape(q['question']).strip(),
                  'correct_answer': html.unescape(q['correct_answer']).strip(),
                  'incorrect_answers': [html.unescape(ans).strip() for ans in q['incorrect_answers']]}
                for q in questions]
    
    return questions



# Example usage
async def main():
    categories = await fetch_categories_async()
    print("Categories:", categories)

    questions = await fetch_questions_async(amount=5, category=9, difficulty="easy")
    print("Questions:", questions)

# Run the example
if __name__ == "__main__":
    asyncio.run(main())






#region Synchronous

def fetch_categories(trivia_database="OpenTDB"):
    if trivia_database == 'OpenTDB':
        url = "https://opentdb.com/api_category.php"
        response = requests.get(url)
        categories = response.json()['trivia_categories']
        return categories
    
# Function to fetch questions from the API
def fetch_questions(trivia_database="OpenTDB", amount=10, category=None, difficulty=None, qtype=None):
    if trivia_database == 'OpenTDB':
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
    
