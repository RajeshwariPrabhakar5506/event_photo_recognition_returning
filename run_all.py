# This is your new 'run_all.py' script

# 1. Import the main function from each of your scripts
from index_faces import main as download_photos_from_sheet
from create_index import create_encodings
from find_matches import find_matches
from send_emails import send_emails

def run_full_process():
    """
    Runs the entire photo recognition workflow from start to finish.
    """
    try:
        # --- Step 1 ---
        print("---------------------------------")
        print("[STEP 1/4] Starting photo download from Google Sheet...")
        download_photos_from_sheet()
        print("[STEP 1/4] Photo download complete.")
        print("---------------------------------\n")

        # --- Step 2 ---
        print("---------------------------------")
        print("[STEP 2/4] Starting face encoding...")
        create_encodings()
        print("[STEP 2/4] Face encoding complete.")
        print("---------------------------------\n")

        # --- Step 3 ---
        print("---------------------------------")
        print("[STEP 3/4] Starting to find matches in event photos...")
        find_matches()
        print("[STEP 3/4] Matching complete.")
        print("---------------------------------\n")

        # --- Step 4 ---
        print("---------------------------------")
        print("[STEP 4/4] Starting email delivery...")
        send_emails()
        print("[STEP 4/4] Email delivery complete.")
        print("---------------------------------\n")

        print("**********")
        print("SUCCESS: All tasks finished.")
        print("**********")

    except Exception as e:
        print(f"\n--- !!! ERROR !!! ---")
        print(f"The process failed with an error: {e}")
        print("Please check the error message above to fix the problem.")

# This makes the script runnable
if __name__ == '__main__':
    run_full_process()