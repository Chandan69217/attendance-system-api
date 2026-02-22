from app.firebase.firebase_init import db
from firebase_admin import firestore
import secrets
import string



def generate_user_id(role: str):

    prefix_map = {
        "student": "S",
        "faculty": "F",
        "admin": "A"
    }

    prefix = prefix_map.get(role.lower(), "U")

    counter_ref = db.collection("counters").document(role)

    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)

        if snapshot.exists:
            count = snapshot.get("count") + 1
        else:
            count = 1

        transaction.set(counter_ref, {"count": count})
        return f"{prefix}{str(count).zfill(3)}"

    transaction = db.transaction()
    return update_counter(transaction)


def generate_dept_id():

    counter_ref = db.collection("counters").document("department")

    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)

        if snapshot.exists:
            count = snapshot.get("count") + 1
        else:
            count = 1

        transaction.set(counter_ref, {"count": count})
        return f"D{str(count).zfill(3)}"

    transaction = db.transaction()
    return update_counter(transaction)


def generate_session_id():

    counter_ref = db.collection("counters").document("session")

    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)

        if snapshot.exists:
            count = snapshot.get("count") + 1
        else:
            count = 1

        transaction.set(counter_ref, {"count": count})
        return f"SE{str(count).zfill(3)}"

    transaction = db.transaction()
    return update_counter(transaction)


def generate_subject_id():

    counter_ref = db.collection("counters").document("subject")

    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)

        if snapshot.exists:
            count = snapshot.get("count") + 1
        else:
            count = 1

        transaction.set(counter_ref, {"count": count})
        return f"SUB{str(count).zfill(3)}"

    transaction = db.transaction()
    return update_counter(transaction)


def generate_class_id():

    counter_ref = db.collection("counters").document("classes")

    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)

        if snapshot.exists:
            count = snapshot.get("count") + 1
        else:
            count = 1

        transaction.set(counter_ref, {"count": count})
        return f"C{str(count).zfill(3)}"

    transaction = db.transaction()
    return update_counter(transaction)


def generate_faculty_attendace_id():

    counter_ref = db.collection("counters").document("faculty_attendance")

    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)

        if snapshot.exists:
            count = snapshot.get("count") + 1
        else:
            count = 1

        transaction.set(counter_ref, {"count": count})
        return f"FA{str(count).zfill(3)}"

    transaction = db.transaction()
    return update_counter(transaction)


def generate_lecture_id():

    counter_ref = db.collection("counters").document("lecture")

    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)

        if snapshot.exists:
            count = snapshot.get("count") + 1
        else:
            count = 1

        transaction.set(counter_ref, {"count": count})
        return f"LEC{str(count).zfill(3)}"

    transaction = db.transaction()
    return update_counter(transaction)


def generate_student_attendance_id():

    counter_ref = db.collection("counters").document("student_attendance")

    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)

        if snapshot.exists:
            count = snapshot.get("count") + 1
        else:
            count = 1

        transaction.set(counter_ref, {"count": count})
        return f"SA{str(count).zfill(3)}"

    transaction = db.transaction()
    return update_counter(transaction)



def generate_random_password(length: int = 8):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))
