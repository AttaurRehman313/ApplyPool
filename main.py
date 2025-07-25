
# perfectly working
from flask import Flask, request, jsonify, render_template
import sqlite3
from openai import OpenAI
from questions import initial_questions, scholarship_questions, internship_questions, common_questions
from dotenv import load_dotenv
import os
import json
import pickle  # For serialization
import re

load_dotenv()
app = Flask(__name__)
OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Function to initialize the SQLite database
def init_db():
    conn = sqlite3.connect('app.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            user_id TEXT NOT NULL,
            questions BLOB NOT NULL,           -- Store a list of questions as a binary object
            answers BLOB NOT NULL,             -- Store a list of answers as a binary object
            appreciation_messages BLOB NOT NULL,-- Store a list of appreciation messages as a binary object
            current_index INTEGER NOT NULL     -- Store the current index
        )
    ''')
    conn.commit()
    conn.close()


init_db()



# Function to update the current_index in the database
def update_current_index(user_id, index):
    try:
        conn = sqlite3.connect('app.db', timeout=10)
        cursor = conn.cursor()
        # Update current_index in the database for the given user_id
        cursor.execute('''
            UPDATE interactions
            SET current_index = ?
            WHERE user_id = ?
        ''', (index, user_id))
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

# Function to store or update interaction in the database
def store_interaction(user_id, questions, answers, appreciation_messages, current_index):
    try:
        conn = sqlite3.connect('app.db', timeout=10)
        cursor = conn.cursor()

        # Serialize the lists before storing them
        serialized_questions = pickle.dumps(questions)
        serialized_answers = pickle.dumps(answers)
        serialized_appreciation_messages = pickle.dumps(appreciation_messages)

        # Check if the user already exists
        cursor.execute('''
            SELECT COUNT(*) FROM interactions WHERE user_id = ?
        ''', (user_id,))
        
        user_exists = cursor.fetchone()[0] > 0  # Returns True if user exists

        if user_exists:
            # Update existing user
            cursor.execute('''
                UPDATE interactions 
                SET questions = ?, 
                    answers = ?, 
                    appreciation_messages = ?, 
                    current_index = ? 
                WHERE user_id = ?
            ''', (serialized_questions, serialized_answers, serialized_appreciation_messages, current_index, user_id))
        else:
            # Insert new user
            cursor.execute('''
                INSERT INTO interactions (user_id, questions, answers, appreciation_messages, current_index)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, serialized_questions, serialized_answers, serialized_appreciation_messages, current_index))

        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"SQLite error: {e}")
    except sqlite3.IntegrityError as e:
        print(f"Integrity error: {e}")
    finally:
        conn.close()

# Add this new function to modify the initial question
def modify_initial_question(question_text):
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"Please modify only the first question to make it more engaging and friendly and also modify it with different career roles every time: '{question_text}'"
        }],
        stream=False
    )
    response_content = completion.choices[0].message.content.strip()
    return response_content





# Function to generate appreciation message without specific next question
def get_appreciation_message(user_answer):
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"The user answered: '{user_answer}'. Respond with an appreciation message."
        }],
        stream=False
    )
    response_content = completion.choices[0].message.content.strip()
    return response_content

# Function to generate appreciation message with static question integration
def get_appreciation_message_with_context(user_answer, next_question_text):
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": (
                f"Here is the user answer: '{user_answer}'. Respond in a friendly, conversational way. "
                f"If the answer is career-related, provide insights about the current market salary and future trends. "
                f"If it's personal or general information, give an appreciation message. "
                f"Always follow up with the next question in a warm tone. "
                f"Appreciation message must be 40-50 words, and should be in the paragraph format"
                f" IF the '{next_question_text}' is  'Does it sound like you?' then do not modify the question but show the same question, else: '{next_question_text}'"
                
            )
        }],
        stream=False
    )
    response_content = completion.choices[0].message.content.strip()
    return response_content

# Function to determine if the user is interested in a scholarship or internship
def determine_user_interest(user_answer):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": (
                f"The user answered: '{user_answer}'. Based on their answer, determine if they are interested in a 'scholarship' or an 'internship'. "
                f"Just respond with either 'scholarship' or 'internship' without any additional text."
            )
        }],
        stream=False
    )
    response_content = completion.choices[0].message.content.strip().lower()
    if 'internship' in response_content:
        return 'internship'
    else:
        return 'scholarship'

@app.route('/api/questionnaire', methods=['POST'])
def questionnaire():
    data = request.get_json()
    user_id = data.get('user_id')
    user_answer = data.get('user_answer')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        conn = sqlite3.connect('app.db', timeout=10)
        cursor = conn.cursor()
        
        # Check if the user exists in the database
        cursor.execute('''SELECT current_index, questions, answers, appreciation_messages FROM interactions WHERE user_id = ?''', (user_id,))
        row = cursor.fetchone()

        if row:
            # Existing user
            current_question_idx = row[0]
            questions_list = pickle.loads(row[1])
            answers_list = pickle.loads(row[2])
            appreciation_messages_list = pickle.loads(row[3])

            # If an answer is provided, append it and determine the next step
            if user_answer:
                answers_list.append(user_answer)

                # Check if we're at question 3 (index 3) to branch into scholarship or internship questions
                if current_question_idx == 3:
                    selection = determine_user_interest(user_answer)
                    next_questions = scholarship_questions if selection == 'scholarship' else internship_questions
                    questions_list.extend(next_questions + common_questions)

                # Increment the question index
                current_question_idx += 1

                # Determine the next question
                if current_question_idx < len(questions_list):
                    next_question = questions_list[current_question_idx]
                    next_question_text = next_question["text"]
                    next_question_key = next_question["key"]
                    appreciation_message = get_appreciation_message_with_context(user_answer, next_question_text)

                    print("----------current question------")
                else:
                    next_question = None
                    next_question_text = ""
                    next_question_key = ""
                    appreciation_message = get_appreciation_message(user_answer)

                # Append the appreciation message
                appreciation_messages_list.append(appreciation_message)

                # Update the interaction in the database
                store_interaction(user_id, questions_list, answers_list, appreciation_messages_list, current_question_idx)

                response_json = {
                    'appreciation_message': appreciation_message
                }

                if next_question:
                    response_json['question_key'] = next_question_key

                return jsonify(response_json), 200
            else:
                # If no answer is provided, prompt the user for the current question
                if current_question_idx < len(questions_list):
                    current_question = questions_list[current_question_idx]
                    question_text = current_question["text"]
                    question_key = current_question["key"]
                    appreciation_message = f"Hello! {question_text}"

                    print("------ run--------")

                    return jsonify({
                        'appreciation_message': appreciation_message,
                        'question_key': question_key
                    }), 200
                else:
                
                    return jsonify({'error': 'No more questions available'}), 400
                
        else:

        
            

            # New user, initialize interaction
            questions_list = initial_questions.copy()
            answers_list = []
            appreciation_messages_list = []


            # # Modify the initial question with the LLM
            # initial_question = questions_list[0]
            # initial_question_text = modify_initial_question(initial_question["text"])
            # initial_question_key = initial_question["key"]


            # Store interaction with initial question index
            store_interaction(user_id, questions_list, answers_list, appreciation_messages_list, 0)

            # Modify the initial question with the LLM
            initial_question = questions_list[0]
            print("\n @@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n",initial_question)
            initial_question_text =modify_initial_question(initial_question["text"])
            initial_question_key = initial_question["key"]
            print('------ enter -----------')


            return jsonify({
                'appreciation_message': f"Hello! {initial_question_text}",
                'question_key': initial_question_key,
                'current_index': 1
            }), 200

    except sqlite3.OperationalError as e:
        return jsonify({'error': f'SQLite error: {e}'}), 500
    finally:
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

