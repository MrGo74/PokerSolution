# Poker 6-Max Texas Hold'em Game

This project is a web-based 6-max Texas Hold'em poker game featuring a single human player against five AI opponents with varying play styles.

The backend is built with Python, Flask, and the PyPokerEngine library, while the frontend is built with standard HTML, CSS, and JavaScript. Communication between the client and server is handled in real-time using WebSockets.

## Requirements

- Python 3.6+

## Installation

1.  **Clone the repository (or download the files).**

2.  **Create and activate a virtual environment (recommended):**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required Python packages:**
    ```sh
    pip install -r requirements.txt
    ```

## How to Play

1.  **Start the Flask server:**
    ```sh
    python app.py
    ```

2.  **Open your web browser** and navigate to the address provided by Flask (usually `http://127.0.0.1:5000`).

3.  Click the "Commencer une nouvelle main" button to start playing.

## Project Structure

- `app.py`: The main Flask application file containing the server-side logic and game management.
- `requirements.txt`: A list of Python dependencies for the project.
- `templates/`: Contains the main HTML file for the game interface.
  - `index.html`: The structure of the web page.
- `static/`: Contains the static assets for the frontend.
  - `css/style.css`: Styles for the game interface.
  - `js/script.js`: Client-side JavaScript for communicating with the server and updating the UI.
- `README.md`: This file.
