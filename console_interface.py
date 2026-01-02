import requests
import html
import os

# Function to clear the console
def clear_console():
    # Para Windows
    if os.name == 'nt':
        os.system('cls')
    # Para Unix/Linux/MacOS
    else:
        os.system('clear')

# Function to fetch available categories from the API
def fetch_categories():
    url = "https://opentdb.com/api_category.php"
    response = requests.get(url)
    categories = response.json()['trivia_categories']
    return categories

# Function to fetch questions from the API
def fetch_questions(amount=10, category=None, difficulty=None, qtype=None):
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

# Main function to interact with the user
def main():
    
    # Display welcome message
    print("Welcome to the TriviaBlitz!")

    # Ask how many competitors are playing
    num_players = int(input("How many players are playing? (1-n): "))
    players = []
    scores = {}
    for i in range(num_players):
        name = input(f"Enter the name of player {i+1}: ")
        players.append(name)
        scores[name] = 0

    clear_console()

    # Ask the user to input parameters
    amount = int(input("\nHow many questions do you want? (1-50): "))
    
    # Select category
    categories = fetch_categories()
    print("Available categories:")
    for category in categories:
        print(f"{category['id']} - {category['name']}")
    print("\nSelect a category (leave blank for random):")
    category_input = input("Category ID: ")
    category = int(category_input) if category_input else None
    
    # Select difficulty
    print("\nChoose a difficulty (easy, medium, hard) or leave blank for random:")
    difficulty = input("Difficulty: ").lower() or None
    
    # Select question type
    print("\nSelect question type:")
    print("1. Multiple Choice (multiple)")
    print("2. True/False (boolean)")
    qtype_input = input("Question type (1 or 2): ")
    qtype = "multiple" if qtype_input == "1" else "boolean" if qtype_input == "2" else None

    time_limit = input("\nSelect time limit (leave blank for infinite):")

    clear_console()

    # Fetch questions from the API
    questions = fetch_questions(amount, category, difficulty, qtype)

    print("\nLet's start the game!\n")

    # Display the fetched questions and answers
    if questions:
        for i, question in enumerate(questions):
            # Unescape HTML entities in the question and answers
            question_text = html.unescape(question['question'])
            correct_answer = html.unescape(question['correct_answer'])
            print(f"[{i+1}] {players[i%num_players]}'s turn: {question_text}")

            # If question contains "one of the following" string print options
            if "of the following" in question_text or "NOT" in question_text or "of these" in question_text:
                options = [html.unescape(ans) for ans in question['incorrect_answers']]
                options.append(correct_answer)
                options.sort()  # Sort options alphabetically
                print("Options:")
                for option in options:
                    print(f"- {option}")                

            # Show answer after pressing enter key
            user_answer = input()

            print(f"Correct answer: {correct_answer}\n")

            correctiness = input("Was the answer correct? (y/n): ")
            if correctiness == "y":
                scores[players[i%num_players]] += 1

            clear_console()
    
    else:
        print("No questions found.")

    # Display the final scores
    print("Final scores:")
    for player, score in scores.items():
        print(f"{player}: {score} points")
    
    # Congratulate the winner
    max_score = max(scores.values())
    winners = [player for player, score in scores.items() if score == max_score]
    if len(winners) == 1:
        print(f"\n{winners[0]} wins!\n")
    else:
        print("\nIt's a tie!\n")

if __name__ == "__main__":
    main()
