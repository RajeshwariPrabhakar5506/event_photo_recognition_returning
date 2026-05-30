import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- CONFIGURATION ---
# For Gmail: Use "smtp.gmail.com" and port 587
# For Outlook/Hotmail: Use "smtp-mail.outlook.com" and port 587
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Your email credentials
# IMPORTANT FOR GMAIL: You cannot use your normal password if 2FA is enabled.
# You must generate and use an "App Password" (see instructions below).
SENDER_EMAIL = "prabhakarrajeshwari306@gmail.com"
SENDER_PASSWORD = "roeb rcig xaqq grpu"

RESULTS_FILE = 'results.json'
# ---------------------

def send_emails():
    print(f"Opening local results ledger: '{RESULTS_FILE}'...")
    try:
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: No match file found: '{RESULTS_FILE}'")
        return
    
    if not results:
        print("Ledger empty. No registered attendee photo matches detected.")
        return

    print(f"Identified {len(results)} recipients with associated event images.")

    # Validation Guardrail
    if SENDER_EMAIL == "your-email@gmail.com" or SENDER_PASSWORD == "your-app-password-or-email-password":
        print("CRITICAL ERROR: Email credentials in 'send_emails.py' are unconfigured.")
        return

    # --- 1. Establish Secure Connection to SMTP Server ---
    try:
        print(f"Connecting to secure SMTP server {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()  # Secure the connection using TLS encryption
        server.ehlo()
        print("Logging in to email account...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("Authentication successful!")
    except Exception as e:
        print(f"CRITICAL LOGIN ERROR: Could not connect or authenticate. details: {e}")
        return

    # --- 2. Iterate and Dispatch Emails ---
    for email_recipient, data in results.items():
        name = data['name']
        photo_paths = data['photos']
        
        if not photo_paths:
            continue

        print(f"Building email for {name} ({email_recipient})...")

        # Create message container
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email_recipient
        msg['Subject'] = "Your Matched Event Photos!"

        # Define HTML body content
        html_body = f"""
        <html>
        <body style="font-family: sans-serif; padding: 20px; line-height: 1.6;">
            <h3 style="color: #2c3e50;">Hello {name}!</h3>
            <p>Our automated facial recognition system matched your face in <strong>{len(photo_paths)}</strong> photos from the event.</p>
            <p>We have attached those matching photos directly to this email. Please enjoy!</p>
            <br/>
            <p style="color: gray; font-size: 11px; border-top: 1px solid #eee; padding-top: 10px;">
                Powered by Event Face Finder AI Engine.
            </p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        # --- 3. Package and Attach Photos ---
        for path in photo_paths:
            try:
                filename = os.path.basename(path)
                with open(path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    
                # Encode payload to Base64 to safely transmit media over email protocols
                encoders.encode_base64(part)
                
                # Add headers for the attachment
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}',
                )
                msg.attach(part)
                print(f"  Attached file: {filename}")

            except FileNotFoundError:
                print(f"  [!] Skipped missing reference asset: {path}")
            except Exception as e:
                print(f"  [!] Issue attaching {path}: {e}")

        # --- 4. Dispatch Email ---
        try:
            server.send_message(msg)
            print(f"  -> Successfully dispatched mail to {email_recipient}")
        except Exception as e:
            print(f"  [!] Delivery failure for {email_recipient}: {e}")

    # --- 5. Cleanly Close Connection ---
    try:
        server.quit()
        print("\nAll emails processed. SMTP connection safely closed.")
    except Exception as e:
        print(f"Error while disconnecting: {e}")

if __name__ == '__main__':
    send_emails()