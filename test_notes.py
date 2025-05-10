import requests
import time

BASE_URL = "http://localhost:5011"

user_id = "user123"
note_title = "My First Note"
note_content = "This is the original content"
note_updated_content = "This is the updated content"

# 1. Create a note
resp = requests.post(f"{BASE_URL}/notes", json={
    "user_id": user_id,
    "title": note_title,
    "content": note_content
})
print(resp.text)
assert resp.status_code == 200
note_id = resp.json()["note_id"]
print(f"[✔] Created note {note_id}")

# Wait for consumer to persist the event
time.sleep(1)

# 2. Get note by ID
resp = requests.get(f"{BASE_URL}/notes/{note_id}")
assert resp.status_code == 200
print(f"[✔] Retrieved note: {resp.json()}")

# 3. Update the note
resp = requests.put(f"{BASE_URL}/notes/{note_id}", json={
    "content": note_updated_content
})
assert resp.status_code == 200
print("[✔] Note update requested")

time.sleep(1)

# 4. Get updated note
resp = requests.get(f"{BASE_URL}/notes/{note_id}")
assert resp.status_code == 200
assert resp.json()["content"] == note_updated_content
print("[✔] Note updated successfully")

# 5. Get note history
resp = requests.get(f"{BASE_URL}/notes/{note_id}/history")
assert resp.status_code == 200
print(f"[✔] Note history: {resp.json()['history']}")

# 6. Get all notes for user
resp = requests.get(f"{BASE_URL}/users/{user_id}/notes")
assert resp.status_code == 200
print(f"[✔] Notes for user {user_id}: {resp.json()}")

# 7. Delete note
resp = requests.delete(f"{BASE_URL}/notes/{note_id}")
assert resp.status_code == 200
print("[✔] Note delete requested")

time.sleep(1)

# 8. Try to get deleted note
resp = requests.get(f"{BASE_URL}/notes/{note_id}")
assert resp.status_code == 410
print("[✔] Note correctly marked as deleted")

# 9. Final check for note history
resp = requests.get(f"{BASE_URL}/notes/{note_id}/history")
assert resp.status_code == 200
print(f"[✔] Final note history: {resp.json()['history']}")
