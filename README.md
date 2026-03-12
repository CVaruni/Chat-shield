Chat-Shield — Spam Detection Platform

SCREENSHOTS 
<img width="702" height="356" alt="ss1" src="https://github.com/user-attachments/assets/4a957bc9-d3cb-40dc-8456-18e182394190" />
<img width="738" height="398" alt="ss2" src="https://github.com/user-attachments/assets/ed8ad9a8-cfc1-4fab-9326-e18de0ae6f21" />
<img width="795" height="433" alt<img width="785" height="395" alt="ss4" src="https://github.com/user-attachments/assets/9c6fa88e-2f18-4bda-a2c1-1edabcee16ad" />

I. Overview
Chat-Shield is a rule-based spam detection system built as a web application that empowers users to verify suspicious messages themselves.
Unlike proprietary spam filters, Chat-Shield operates entirely locally, giving users full transparency into how detection works and complete control over their data.

II. Problem Statement
Most spam filters are background services with no transparency — users have no insight into detection logic, and their data is often sent to centralized servers. 
Chat-Shield solves this by providing:
1. An interpretable, keyword-driven detection engine
2. A privacy-first design (all processing is local)
3. A scalable dataset that can power future ML-based enhancements

III. Features
1. Real-time spam/ham classification via keyword matching
2. Intuitive web interface (Enter sender + message → instant result)
3. SQLite database to log spam history with timestamps
4. Message history viewer for tracking flagged messages
5. Manual reporting module for dataset building
6. Plotly trend visualizations
7. Zero external data transmission 

IV. How It Works
The detection algorithm uses a keyword-matching procedure:
1. User inputs sender details and message content
2. Message is tokenized into lowercase words
3. Each token is compared against a spam-keyword dictionary
4. If keyword hit count > threshold → classified as SPAM
5. Else → classified as NOT SPAM
6. Result + metadata stored in SQLite database

V. Performance Metrics
Tested on 100 sample messages (60 spam, 40 ham):
Metric                  Value
Accuracy                90%
Precision               88%
Recall                  92%
Avg. Response Time      0.8s

VI. Project Structure
Chat-Shield/
│
├── app.py                  # Main Streamlit app
├── spam_detector.py        # Keyword matching logic
├── database.py             # SQLite operations
├── keywords.py             # Spam keyword dictionary
├── requirements.txt        # Dependencies
└── README.md

VII.  Installation & Setup

1. Clone the repository - git clone https://github.com/CVaruni/Chat-shield.git
                          cd Chat-shield
2. Install dependencies - pip install -r requirements.txt
3. Run the app - streamlit run app.py
4. Open your browser - at http://localhost:8501

VIII.  Sample Usage
Input                                                                      Result
"Congratulations! You've won a free iPhone. Click here to claim now."    🔴 SPAM
"Hey, are we still meeting at 3pm tomorrow?"                             🟢 NOT SPAM
"URGENT: Your account has been compromised. Verify immediately."         🔴 SPAM
