1. Configure Google Cloud Platform (GCP) Credentials
Go to the Google Cloud Console.

Create a new project and enable both the Google Sheets API and Google Drive API.

Navigate to IAM & Admin > Service Accounts, create a service account, and generate a JSON key.

Save the downloaded JSON file as credentials.json in your root project folder.

Open your Google Form's response spreadsheet and your Drive upload folder, and Share both with the client_email found inside your credentials.json (give it Viewer permissions).

2. Adjust Google Form Settings
Open your Google Form editor.

Navigate to Settings > Responses.

Change Collect email addresses to Verified. This ensures your spreadsheet captures accurate Gmail records instead of text inputs prone to spelling errors.

3. Create a Gmail App Password
Navigate to your Google Account Security Dashboard.

Enable 2-Step Verification.

Search for App Passwords, generate a key titled Event Matcher App, and copy the 16-character code snippet provided.

⚙️ Configuration & Execution
Open app.py and modify the script variables with your environment constants:

Python
# Insert your spreadsheet ID (found in your Google Sheet browser URL)
SPREADSHEET_ID = 'PASTE_YOUR_SPREADSHEET_ID_HERE' 

# Set your email delivery credentials
SENDER_EMAIL = "your-distribution-email@gmail.com"
SENDER_PASSWORD = "your-16-character-app-password"
Drop your unsorted event photos inside the event_photos/ folder, and trigger the script execution from your terminal:

Bash
python app.py
🧠 Technical Concept: Why HOG?
The Histogram of Oriented Gradients (HOG) technique works by transforming image pixels into gradient vectors that look at changes in light intensity along edge lines.

Gradient Computation: Evaluates directional changes in brightness to isolate contours (eyes, nose, jawline).

Cell Histograms: Aggregates edge directions inside micro-regions.

Block Normalization: Balances contrast shifts caused by unpredictable flash photography or shadows during live outdoor events.

This architecture offers a lightweight alternative to deep convolutional neural network (CNN) detection layers, enabling real-time classification directly on standard laptop processors.
