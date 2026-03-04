from recognizer import FaceRecognizer
from database import delete_user as delete_user_from_db
from cloud_sync import upload_file
from security_logger import log_event


def delete_user_flow():

    name = input("Enter username to delete: ").strip()

    if not name:
        print("Invalid username.")
        return

    recognizer = FaceRecognizer()

    # Check if user exists in encodings
    if name not in recognizer.data:
        print("User not found in encodings.")
        return

    # Delete from recognizer (embeddings)
    recognizer.delete_user(name)
    print(f"{name} removed from encodings.")

    # Delete from database (if your DB tracks users)
    try:
        delete_user_from_db(name)
        print(f"{name} removed from database.")
    except:
        print("User removed from encodings (DB removal skipped or not required).")

    # Upload updated encodings to cloud
    try:
        upload_file("encodings.pkl", "encodings.pkl")
        print("Updated encodings uploaded to cloud.")
    except:
        print("Cloud upload skipped or failed.")

    # Log deletion event
    try:
        log_event(
            name,
            0,
            "USER_DELETED",
            "ADMIN_ACTION"
        )
    except:
        pass

    print("Deletion completed successfully.")


if __name__ == "__main__":
    delete_user_flow()