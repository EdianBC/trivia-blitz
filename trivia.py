import os
import html
import aiohttp
import asyncio
import pandas as pd
import random

available_trivia_databases = ['OpenTDB', 'OpenTriviaQA']

#region Fetch Cat Async
async def fetch_categories_async(trivia_database="OpenTriviaQA"):
    if trivia_database == 'OpenTDB':
        return await fetch_categories_opentdb()
    elif trivia_database == 'OpenTriviaQA':
        return await fetch_categories_opentriviaqa()
                

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


async def fetch_categories_opentriviaqa():
    folder_path = "OpenTriviaQAKaggle"
    categories = []

    loop = asyncio.get_event_loop()
    file_names = await loop.run_in_executor(None, os.listdir, folder_path)

    for file_name in file_names:    
        categories.append(os.path.splitext(file_name)[0]) # Remove the .csv extension

    return categories


#region Fetch Qs Async

# Must return list of dictionaries with keys: 'question':str, 'correct_answer':str, 'incorrect_answers':list[str]
async def fetch_questions_async(trivia_database="OpenTriviaQA", amount=10, category=None, difficulty=None, qtype=None):
    if trivia_database == "OpenTDB":
        return await fetch_questions_opentdb(amount, category, difficulty, qtype)
    elif trivia_database == "OpenTriviaQA":
        return await fetch_questions_opentriviaqa(amount, category)

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


async def fetch_questions_opentriviaqa(amount=10, categories=None):
    folder_path = "OpenTriviaQAKaggle"
    all_files = os.listdir(folder_path)
    
    # Filtrar archivos CSV
    csv_files = [f for f in all_files if f.endswith(".csv")]
    
    # Si no se especifican categorías, usar todas las preguntas
    if not categories:
        all_questions = []
        for file in csv_files:
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)
            all_questions.extend(df.to_dict(orient="records"))
        
        # Seleccionar aleatoriamente las preguntas
        selected_questions = random.sample(all_questions, min(amount, len(all_questions)))
    
    else:
        # Filtrar archivos según las categorías especificadas
        selected_files = [f"{category}.csv" for category in categories if f"{category}.csv" in csv_files]
        if not selected_files:
            return []  # Si no hay archivos para las categorías, retornar lista vacía
        random.shuffle(selected_files)

        # Calcular cuántas preguntas tomar de cada categoría
        num_categories = len(selected_files)
        base_amount = amount // num_categories
        remainder = amount % num_categories
        
        selected_questions = []
        for file in selected_files:
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)
            questions = df.to_dict(orient="records")
            
            # Seleccionar preguntas de esta categoría
            num_questions = base_amount + (1 if remainder > 0 else 0)
            remainder -= 1
            selected_questions.extend(random.sample(questions, min(num_questions, len(questions))))
    
    # Formatear las preguntas según el nuevo formato
    formatted_questions = []
    for q in selected_questions:
        question_text = html.unescape(str(q.get("Questions", ""))).strip()
        correct_answer = html.unescape(str(q.get("Correct", ""))).strip()
        incorrect_answers = [
            html.unescape(str(ans)).strip()
            for ans in [str(q.get("A", "")), str(q.get("B", "")), str(q.get("C", "")), str(q.get("D", ""))]
            if str(ans).strip() and str(ans).strip() != correct_answer and str(ans).strip() != "nan"
        ]
        formatted_questions.append({
            "question": question_text,
            "correct_answer": correct_answer,
            "incorrect_answers": incorrect_answers
        })
    
    return random.shuffle(formatted_questions)
 

# Example usage
async def main():
    categories = await fetch_categories_async()
    print("Categories:", categories)

    questions = await fetch_questions_async(amount=5, category=None, difficulty="easy")
    print("Questions:", questions)

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
