# 🥤 Bubblelytics: The AI Bubble Tea Counter

Tired of not knowing exactly how many bubbles are in your tea? Worry no more! We built a polished, multi-page web application that uses computer vision to analyze your tea and a dashboard to track the most bubbly submissions.

### Live Application Features
-   **Modern, Multi-Page Interface:** A clean and professional design with separate pages for Home, Analysis, a Stats Dashboard, and a technical "How It Works" deep-dive.
-   **AI-Powered Analysis:** Upload a photo, and our OpenCV-powered backend will detect and count the bubbles in seconds.
-   **Interactive Dashboard:** The leaderboard is now a full dashboard showing key statistics like total teas analyzed, average bubble count, and the all-time high score.
-   **Visual Feedback:** See exactly how the AI identified the bubbles with detailed process and final result images.

## Technical Stack
-   **Backend:** Python, Flask
-   **Frontend:** HTML, Tailwind CSS
-   **Image Processing:** OpenCV, NumPy, Matplotlib
-   **Database:** SQLite

## How to Run
1.  **Set up Environment:**
    ```bash
    # Create a virtual environment
    python -m venv venv

    # Activate it
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install Flask opencv-python numpy matplotlib
    ```

3.  **Run the App:**
    ```bash
    # This will initialize the database and start the server
    python app.py
    ```

4.  **View in Browser:**
    Open `http://127.0.0.1:5000` in your web browser.

---
Made with ❤️ and lots of bubbles.