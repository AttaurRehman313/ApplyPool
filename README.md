# Applypool

Applypool is a Flask-based web application that interactively guides users through a personalized questionnaire for scholarships and internships. It uses OpenAI's GPT models to generate engaging questions and appreciation messages, adapting dynamically to user responses.

---

## Project Structure

```
.
├── .env
├── .gitignore
├── app.db
├── main.py
├── questions.py
├── req.txt
├── templates/
│   └── index.html
└── env/
    └── ... (Python virtual environment files)
```

### File Descriptions

- **[main.py](main.py)**  
  The main Flask application. Handles API endpoints, database operations, OpenAI integration, and questionnaire logic.

- **[questions.py](questions.py)**  
  Contains the lists of questions for the initial, scholarship, internship, and common sections of the questionnaire.

- **[req.txt](req.txt)**  
  Lists all Python dependencies required to run the project. Install with `pip install -r req.txt`.

- **[.env](.env)**  
  Stores environment variables, such as your OpenAI API key.  
  **Example:**  
  ```
  OPEN_AI_KEY=your_openai_api_key_here
  ```

- **[.gitignore](.gitignore)**  
  Specifies files and directories to be ignored by git, such as `.env` and the `env/` virtual environment.

- **[app.db](app.db)**  
  The SQLite database file used to store user interactions and progress.

- **[templates/index.html](templates/index.html)**  
  The front-end HTML template for the interactive questionnaire UI.

- **env/**  
  Your Python virtual environment directory (not tracked by git).

---

## Setup Instructions

1. **Clone the repository**  
   ```sh
   git clone <your-repo-url>
   cd Applypool
   ```

2. **Create and activate a virtual environment**  
   ```sh
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**  
   ```sh
   pip install -r req.txt
   ```

4. **Set up your `.env` file**  
   ```
   OPEN_AI_KEY=your_openai_api_key_here
   ```

5. **Run the application**  
   ```sh
   python main.py
   ```
   Visit [http://localhost:5000](http://localhost:5000) in your browser.

---

## Usage

- The web UI will guide users through a series of questions.
- Answers and progress are stored in the SQLite database.
- The backend uses OpenAI's GPT models to generate dynamic and engaging content.

---

## License

MIT License

---

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
-
