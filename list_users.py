from recognizer import FaceRecognizer
from security_logger import log_event


def list_users():

    recognizer = FaceRecognizer()

    users = recognizer.data

    if not users:
        print("\nNo users registered in the system.\n")
        return

    print("\n=== REGISTERED USERS ===\n")

    for i, (name, info) in enumerate(users.items(), start=1):
        num_embeddings = len(info["embeddings"])
        print(f"{i}. {name}  |  Embeddings: {num_embeddings}")

    print("\n-------------------------")
    print(f"Total Users: {len(users)}\n")

    # Optional: Log admin action
    try:
        log_event(
            "ADMIN",
            0,
            "VIEW_USERS",
            "ADMIN_ACTION"
        )
    except:
        pass


if __name__ == "__main__":
    list_users()