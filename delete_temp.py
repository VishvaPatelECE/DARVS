from database import delete_user
from recognizer import FaceRecognizer

delete_user("Vishva")

rec = FaceRecognizer()
rec.delete_user("Vishva")

print("User deleted completely.")