import face_recognition
import glob
import os
import pickle
import json
import time

# --- CONFIGURATION ---
ENCODINGS_FILE = 'encodings.pkl'
EVENT_PHOTOS_FOLDER = 'event_photos'
RESULTS_FILE = 'results.json'

# How strict the matching is. 
# Lower number = stricter. 0.6 is a good default.
MATCH_TOLERANCE = 0.6
# ---------------------

def find_matches():
    # --- 1. LOAD KNOWN FACES ---
    print(f"Loading known face encodings from '{ENCODINGS_FILE}'...")
    try:
        with open(ENCODINGS_FILE, 'rb') as f:
            known_face_data = pickle.load(f)
    except FileNotFoundError:
        print(f"ERROR: Encodings file not found: '{ENCODINGS_FILE}'")
        print("Please run the 'create_index.py' script first.")
        return
    except Exception as e:
        print(f"Error loading encodings file: {e}")
        return

    # Create separate lists for encodings and the user data
    known_encodings = [data['encoding'] for data in known_face_data]
    known_user_info = [data for data in known_face_data] # name, email
    
    if not known_encodings:
        print("No faces found in the encodings file. Exiting.")
        return
        
    print(f"Loaded {len(known_encodings)} known faces.")

    # --- 2. PREPARE FOR RESULTS ---
    # This dictionary will store our results
    # Format: { 'jane@example.com': {'name': 'Jane Doe', 'photos': set(['img1.jpg', 'img2.jpg'])}, ... }
    results = {}
    
    # Pre-populate the results dict with all known users
    for data in known_user_info:
        results[data['email']] = {
            'name': data['name'],
            'photos': set() # A 'set' automatically handles duplicates
        }

    # --- 3. PROCESS EVENT PHOTOS ---
    event_image_paths = glob.glob(os.path.join(EVENT_PHOTOS_FOLDER, '*.*'))
    # Filter for common image types
    event_image_paths = [p for p in event_image_paths if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not event_image_paths:
        print(f"No event photos found in '{EVENT_PHOTOS_FOLDER}'.")
        return

    print(f"\nStarting recognition on {len(event_image_paths)} event photos...")
    start_time = time.time()

    for (i, img_path) in enumerate(event_image_paths):
        img_name = os.path.basename(img_path)
        print(f"  Processing photo [{i+1}/{len(event_image_paths)}] {img_name}...")
        
        # Load the event image
        try:
            event_image = face_recognition.load_image_file(img_path)
        except Exception as e:
            print(f"    [!] Could not load image {img_name}. Skipping. Error: {e}")
            continue
            
        # Find all faces in the event image
        # Using 'cnn' is more accurate but MUCH slower. 'hog' is faster.
        # Use 'cnn' if you have a GPU (pip install dlib-models)
        event_face_locations = face_recognition.face_locations(event_image, model='hog')
        event_face_encodings = face_recognition.face_encodings(event_image, event_face_locations)

        if not event_face_encodings:
            print(f"    No faces found in {img_name}.")
            continue
            
        print(f"    Found {len(event_face_encodings)} face(s) in {img_name}.")

        # Loop through each face found in this one event photo
        for event_encoding in event_face_encodings:
            
            # Compare this face to ALL known faces
            matches = face_recognition.compare_faces(known_encodings, event_encoding, tolerance=MATCH_TOLERANCE)
            
            # Check for any match
            # This returns a list like [False, True, False]
            if True in matches:
                # Find which user it was
                match_index = matches.index(True)
                
                # Get the matched user's info
                matched_user = known_user_info[match_index]
                name = matched_user['name']
                email = matched_user['email']
                
                print(f"      -> Match found for: {name} ({email})")
                
                # Add this photo to that user's list
                results[email]['photos'].add(img_path)

    # --- 4. SAVE RESULTS ---
    print("\nRecognition complete.")
    
    # Convert sets to lists so JSON can save them
    final_results = {}
    for email, data in results.items():
        if data['photos']: # Only include users who were found
            final_results[email] = {
                'name': data['name'],
                'photos': list(data['photos'])
            }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(final_results, f, indent=4)

    total_time = time.time() - start_time
    print(f"Saved {len(final_results)} users' results to '{RESULTS_FILE}'.")
    print(f"Total processing time: {total_time:.2f} seconds.")

if __name__ == '__main__':
    find_matches()

    