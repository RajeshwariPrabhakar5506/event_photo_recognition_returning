import face_recognition
import glob
import os
import pickle

# --- CONFIGURATION ---
PHOTOS_FOLDER = 'reference_photos'
ENCODINGS_FILE = 'encodings.pkl'
# ---------------------

def create_encodings():
    print(f"Starting to index faces in '{PHOTOS_FOLDER}'...")
    
    # This will hold all our data
    # Format: [ (name, email, encoding_array), ... ]
    known_face_data = []

    # Get a list of all .jpg files in the folder
    image_paths = glob.glob(os.path.join(PHOTOS_FOLDER, '*.jpg'))
    
    if not image_paths:
        print(f"No .jpg photos found in '{PHOTOS_FOLDER}'.")
        print("Please run the 'index_faces.py' script first to download photos.")
        return

    print(f"Found {len(image_paths)} photos to process.")

    # Loop over each photo
    for (i, image_path) in enumerate(image_paths):
        # Extract the person's name and email from the filename
        # e.g., "Jane Doe_jane@example.com.jpg"
        filename = os.path.basename(image_path)
        
        try:
            # Split the filename to get name and email
            base_name = os.path.splitext(filename)[0]
            name, email = base_name.split('_')
        except Exception:
            print(f"  [!] Skipping {filename}. Filename is not in 'Name_Email.jpg' format.")
            continue
            
        print(f"  Processing [{i+1}/{len(image_paths)}] {name} ({email})...")

        # Load the image
        image = face_recognition.load_image_file(image_path)
        
        # Find all faces in the image.
        # We assume the user uploaded a clear photo with ONE face.
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) > 0:
            # Get the first (and hopefully only) face encoding
            user_face_encoding = face_encodings[0]
            
            # Add the data to our list
            user_data = {
                "name": name,
                "email": email,
                "encoding": user_face_encoding
            }
            known_face_data.append(user_data)
        else:
            print(f"  [!] WARNING: No face found for {name}. Skipping this photo.")

    # --- 4. SAVE THE ENCODINGS ---
    print(f"\nProcessing complete. Found {len(known_face_data)} faces.")
    print(f"Saving encodings to '{ENCODINGS_FILE}'...")

    # Open the file in "write binary" mode and save the data
    with open(ENCODINGS_FILE, 'wb') as f:
        pickle.dump(known_face_data, f)
        
    print("Done.")

if __name__ == '__main__':
    create_encodings()