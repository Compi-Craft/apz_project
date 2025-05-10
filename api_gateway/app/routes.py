from flask import jsonify, request, redirect, url_for, render_template, make_response, abort, g, flash
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from app.forms import RegistrationForm, LoginForm, NoteForm, UpdateNoteForm
from app import app
import requests
import redis

app.config['JWT_SECRET_KEY'] = 'your_secret_key'
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

jwt = JWTManager(app)

MICROSERVICE_URL = "http://localhost:5001"
NOTE_SERVICE_URL = "http://localhost:5011"

host_name, port = "localhost", 6380
redis_client = redis.Redis(host=host_name, port=port, db=0, decode_responses=True)

class CurrentUser:
    def __init__(self, identity=None):
        self.identity = identity
        self.is_authenticated = identity is not None

    def __repr__(self):
        return f"<CurrentUser {self.identity}>"

@app.before_request
def load_current_user():
    try:
        verify_jwt_in_request()
        identity = get_jwt_identity()
        g.current_user = CurrentUser(identity)
    except Exception:
        g.current_user = CurrentUser(None)

@app.before_request
def check_blacklist():
    """Check if the incoming JWT is blacklisted."""
    token = request.cookies.get('access_token_cookie')
    if token:
        if redis_client.get(token):
            return jsonify({"msg": "Token is unavailable"}), 401

@app.context_processor
def inject_user():
    return dict(current_user=g.get('current_user', None))

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/signup", methods=["POST", "GET"])
def signup():
    """Signup route that handles user registration."""
    try:
        verify_jwt_in_request(optional=True)
        if get_jwt_identity():
            return redirect(url_for("home"))
    except Exception:
        pass
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        try:
            response = requests.post(f'{MICROSERVICE_URL}/signup', params={'username': username, 'email': email, 'password': password})
            return redirect(url_for("login"))
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    """Login route that handles user authentication."""
    try:
        verify_jwt_in_request(optional=True)
        if get_jwt_identity():
            return redirect(url_for("home"))
    except Exception:
        pass
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        response = requests.post(f'{MICROSERVICE_URL}/login', params={'email': email, 'password': password})
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            response = make_response(redirect(url_for('home')))
            print(access_token)
            response.set_cookie('access_token_cookie', access_token, httponly=True, secure=True, samesite='Lax')
            return response
    return render_template('login.html', title='Login', form=form)

@app.route("/logout", methods=["POST", "GET"])
@jwt_required()
def logout():
    access_token = request.cookies.get('access_token_cookie')
    if not access_token:
        return jsonify({"error": "Missing access token cookie"}), 400
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.post(f'{MICROSERVICE_URL}/logout', headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Failed to logout from the microservice"}), response.status_code
    response = make_response(redirect(url_for('home')))
    response.delete_cookie('access_token_cookie')
    flash("Logged out successfully", "success")
    return response


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route("/notes", methods = ["GET"])
@jwt_required()
def notes():
    user_id = get_jwt_identity()
    access_token = request.cookies.get('access_token_cookie')
    if not access_token:
        return jsonify({"error": "Missing access token"}), 401
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(f"{NOTE_SERVICE_URL}/users/{user_id}/notes", headers=headers)
    except requests.RequestException as e:
        return jsonify({"error": "Failed to contact notes service", "details": str(e)}), 500
    if response.status_code != 200:
        abort(403)
    notes = response.json()
    print(notes)
    return render_template("notes.html", notes = notes, title = "Notes")

@app.route("/new_note", methods = ["GET", "POST"])
@jwt_required()
def new_note():
    form = NoteForm()
    if form.validate_on_submit():
        user_id = get_jwt_identity()
        access_token = request.cookies.get('access_token_cookie')
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.post(f"{NOTE_SERVICE_URL}/notes", headers=headers, json={"user_id": user_id,
                                                                                       "title": form.title.data,
                                                                                       "content": form.content.data})
        if response.status_code != 200:
            abort(response.status_code)
        flash("Note created", "success")
        return redirect(url_for("notes"))
    return render_template("create_note.html", form = form, title = "Create Note", legend="Create Note")

@app.route("/view_note/<note_id>", methods = ["GET", "POST"])
@jwt_required()
def view_note(note_id):
    form = UpdateNoteForm()
    access_token = request.cookies.get('access_token_cookie')
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    if form.validate_on_submit():
        response = requests.put(f"{NOTE_SERVICE_URL}/notes/{note_id}", headers=headers, json={"content": form.content.data})
        if response.status_code != 200:
            abort(response.status_code)
        flash("Note updated", "success")
        return redirect(url_for("notes"))
    note = requests.get(f"{NOTE_SERVICE_URL}/notes/{note_id}", headers=headers).json()
    form.content.data = note.get("content")
    return render_template("view_note.html", form = form, title = "View Note", legend=note.get("title"))
