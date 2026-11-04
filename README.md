# AI Interview Practice

A web app that helps job seekers practice interviews and **understand exactly where their answers go wrong**.

In a real interview you rarely get feedback. This app asks you interview questions one by one, scores your answer on five fixed criteria with a **reason for every score**, shows the **type of mistake**, gives a **model answer**, and lets you **rewrite and re-evaluate** to prove you improved. At the end you get a report and downloadable revision notes.

---

## Why not just ask ChatGPT or Google?

ChatGPT and Google give you the answer to a question. This app **checks your answer**.

| | Chat / search | AI Interview Practice |
|---|---|---|
| Who answers | The AI answers, you read | **You answer**, the app evaluates |
| Feedback | Different format every time | **Same 5 criteria every time**, each with a reason |
| Mistakes | You have to find them yourself | **Mistake types** and **missed points** are listed |
| Progress | Not tracked | **Before vs After** score after you rewrite |
| Effort | You must write good prompts | Guided flow, **no prompts needed** |
| Output | A chat history | **Final report** and **revision notes** |

---

## Features

- **6 topics, 30 questions:** Java, Python, HR, JavaScript, SQL, DSA (5 questions each)
- **5-criteria scoring (0 to 10):** correctness, clarity, completeness, structure, relevance, each with a written reason
- **Mistake tagging:** `wrong_concept`, `incomplete`, `unclear`, `no_example`, `off_topic`
- **Missed points** and **improvement steps** for every answer
- **Your answer vs model answer** side by side
- **Improve my answer:** rewrite and re-evaluate, then see **Before vs After**
- **Final report:** overall score, per-criterion averages, strength, weakest area, question-wise review
- **Revision notes:** downloadable `.txt` with the model answers for weak questions (average score below 7)
- **Automatic fallback:** if the AI is busy or unreachable, the app switches to an offline evaluator so it keeps working
- **No installation of packages:** the backend uses only Python's standard library

---

## How it works

```
Browser (index.html)                 Python server (backend.py)              Google Gemini
  choose topic  ───────────────►  GET /api/questions
  write answer  ───────────────►  POST /api/evaluate  ───────────────►  generateContent
                                         │                                   │
                                         │◄──────────── JSON feedback ◄──────┘
                                         │
                                         └── if Gemini fails or key = "offline"
                                             → local rule-based evaluator
  scores, reasons, mistakes, model answer, report  ◄───────────────────
```

1. Pick a topic and start the interview.
2. Answer each question in the text box and click **Evaluate Answer**.
3. Read the scores, reasons, mistake types, missed points and the model answer.
4. Optionally rewrite your answer and click **Re-evaluate** to see your improvement.
5. After the last question, open the **final report** and download your **revision notes**.

---

## Project structure

```
interview-app/
├── backend.py    # Python server: questions, Gemini call, offline evaluator
├── index.html    # Frontend: HTML + CSS + JavaScript in one file
└── README.md
```

Both `backend.py` and `index.html` must be in the **same folder**, with exactly these names.

---

## Requirements

- **Python 3.8 or newer** (download from [python.org](https://www.python.org/downloads/); tick **"Add python.exe to PATH"** while installing)
- A modern browser (Chrome, Edge, Firefox)
- **No `pip install` needed**
- A free **Gemini API key** is optional (see below). Without it you can still use the offline mode.

---

## Setup and run

1. Put `backend.py` and `index.html` in one folder, for example `interview-app`.
2. Open a terminal in that folder.
3. Start the server:

   ```
   python backend.py
   ```

   If `python` is not recognized on Windows, use:

   ```
   py backend.py
   ```

4. You should see:

   ```
   Server running at: http://localhost:8000  (press Ctrl + C to stop)
   ```

5. Open **http://localhost:8000** in your browser.
6. Type your Gemini API key (or the word `offline`) in the box at the top, choose a topic and click **Start Interview**.

To stop the server, press `Ctrl + C` in the terminal.

> Always open the app through `http://localhost:8000`. Double-clicking `index.html` will not work because the page needs the backend.

---

## Getting a Gemini API key

1. Go to **https://aistudio.google.com/apikey** and sign in with a Google account.
2. Click **Create API key**.
3. Copy the key and paste it into the box at the top of the app.

Treat the key like a password. Do not share it or post it in screenshots.

---

## Offline mode

Type **`offline`** in the key box to skip Gemini completely. The app then uses a built-in rule-based evaluator:

- Every question has a model answer and five key points, each with keywords.
- The score is based on how many key points your answer covers, plus its length and structure.
- It works without internet and responds instantly.

The same evaluator is used automatically when Gemini is busy, slow, or returns an unreadable response. In that case the first improvement step is marked: *"the AI was busy, so this is offline rule-based feedback."*

**Limits of offline mode:** it matches keywords, so it is less flexible than the AI. Write your answers in English and use the proper technical terms (for example "LIFO", "closure", "inner join").

---

## How the AI evaluation works

For every answer the server asks Gemini to return **only JSON** in a fixed format:

```json
{
  "scores": {"correctness": 0, "clarity": 0, "completeness": 0, "structure": 0, "relevance": 0},
  "reasons": {"correctness": "...", "clarity": "...", "completeness": "...", "structure": "...", "relevance": "..."},
  "mistake_types": ["wrong_concept | incomplete | unclear | no_example | off_topic"],
  "missing_points": ["..."],
  "model_answer": "...",
  "improvement_steps": ["..."]
}
```

The frontend turns this JSON into the score bars, reasons, tags and side-by-side answers. The offline evaluator returns the same structure, so the page works the same either way.

Settings at the top of `backend.py`:

| Setting | Default | Meaning |
|---|---|---|
| `MODEL` | `gemini-3.8-flash` | Gemini model name |
| `ATTEMPTS` | `2` | How many times to try Gemini before falling back |
| `REQUEST_TIMEOUT` | `30` | Seconds to wait for one try |
| `PORT` | `8000` | Port of the local server |

Google retires and renames models over time. If you see a `404 ... model not found` error, open `backend.py`, update `MODEL` to a model currently listed in Google AI Studio, save, and restart the server.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognized | Install Python from python.org with "Add to PATH", or run `py backend.py`. Restart the terminal afterwards. |
| `can't open file ... backend.py` | The file is probably named `backend.py.py`. Rename it to exactly `backend.py` (same for `index.html`). Turn on **View > File name extensions** in Windows Explorer to see the real names. |
| "Could not connect to the backend" | The server is not running. Run `python backend.py` and open `http://localhost:8000`. |
| `index.html not found` | Keep `backend.py` and `index.html` in the same folder. |
| Page shows old design or old text | Hard refresh with `Ctrl + Shift + R`. If you changed `backend.py`, stop the server (`Ctrl + C`) and start it again. |
| "Please enter your API key at the top" | Paste a Gemini key, or type `offline`. |
| `API error 400 / 401 / 403` | The key is invalid or restricted. Create a new key and paste it again, without spaces. |
| `API error 404 ... model` | The model name is outdated. Update `MODEL` in `backend.py` and restart. |
| `503 ... high demand` or "read operation timed out" | Gemini is overloaded. The app retries and then falls back to offline feedback automatically. You can also wait a minute and try again. |
| `Address already in use` | Another copy of the server is running. Close it, or change `PORT` in `backend.py`. |
| `SyntaxError` after editing `backend.py` | A quote or bracket was damaged while editing. Check the line the error points to. |

---

## Privacy and security notes

- The API key you type is saved in your **browser's localStorage** so you do not have to type it again, and it is sent only to your own local server, which forwards it to Google.
- Your answers are sent to Google Gemini when you use AI mode. They are not sent anywhere in offline mode.
- The server listens on all network interfaces (`0.0.0.0`). On a shared network, other devices could reach it. Change it to `127.0.0.1` in `backend.py` if you want it reachable only from your own computer.
- This is a demo project: there is no login, no database and no rate limiting.

---

## Customizing

**Add a topic or question**

1. In `backend.py`, add the questions to `QUESTIONS`.
2. Add a matching entry to `KB_LIST` for each question, **in the same order**: a `model` answer and five `points`, each with a label and a list of lowercase keywords.
3. Restart the server. The topic appears in the dropdown automatically.

**Change the design**

All styling is in the `<style>` block of `index.html`. The HTML and JavaScript do not need to change for a new look.

---

## Known limitations

- No login or saved history: progress exists only for the current session.
- Questions are fixed (6 topics, 5 each).
- Offline evaluation is keyword-based, so it is less accurate than AI evaluation.
- Text answers only; no voice input.
- The interface and questions are in English.

## Future improvements

- Secure login and a database to track progress across sessions and devices
- Voice answers with speaking feedback (filler words, pace)
- Questions personalized to a resume or job role
- More topics and difficulty levels
- Hindi and other regional languages

---

## Question sources

The question list was assembled from common fresher interview question lists published by Naukri, PW Skills, GreatFrontend, Talentedge and FACE Prep. The model answers were written for this project.
