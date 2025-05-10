from flask import jsonify, request, redirect, url_for, render_template, make_response, abort, g, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.forms import RegistrationForm, LoginForm, NoteForm, UpdateNoteForm
from app import app, redis_client, jwt
from app.models import CurrentUser
import random
from app.get_services import get_service_links_by_name
import requests

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

@jwt.expired_token_loader
def custom_expired_token_callback(jwt_header, jwt_payload):
    flash("Your session expired, login again to continue", "warning")
    return redirect(url_for('login'))

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
        selected_service = get_service_links_by_name("auth_service")
        if selected_service is None:
            abort(503)
        response = requests.post(f'{selected_service}/signup', params={'username': username, 'email': email, 'password': password})
        if response.status_code == 200:
            flash("You registered", "success")
            return redirect(url_for("login"))
        elif response.status_code == 400:
            flash("Email already taken", "warning")
            return redirect(url_for("signup"))
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
        selected_service = get_service_links_by_name("auth_service")
        if selected_service is None:
            abort(503)
        response = requests.post(f'{selected_service}/login', params={'email': email, 'password': password})
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            response = make_response(redirect(url_for('home')))
            response.set_cookie('access_token_cookie', access_token, httponly=True, secure=True, samesite='Lax')
            flash("You logged in", "success")
            return response
        elif response.status_code == 401:
            flash("User not found or wrong password", "warning")
            return redirect(url_for("login"))
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
    selected_service = get_service_links_by_name("auth_service")
    if selected_service is None:
        abort(503)
    response = requests.post(f'{selected_service}/logout', headers=headers)
    if response.status_code != 200:
        abort(response.status_code)
    response = make_response(redirect(url_for('home')))
    response.delete_cookie('access_token_cookie')
    flash("Logged out successfully", "success")
    return response

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
    selected_service = get_service_links_by_name("notes_service")
    if selected_service is None:
        abort(503)
    response = requests.get(f"{selected_service}/users/{user_id}/notes", headers=headers)
    if response.status_code != 200:
        abort(response.status_code)
    notes = response.json()
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
        selected_service = get_service_links_by_name("notes_service")
        if selected_service is None:
            abort(503)
        response = requests.post(f"{selected_service}/notes", headers=headers, json={"user_id": user_id,
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
    selected_service = get_service_links_by_name("notes_service")
    if form.validate_on_submit():
        if selected_service is None:
            abort(503)
        response = requests.put(f"{selected_service}/notes/{note_id}", headers=headers, json={"content": form.content.data})
        if response.status_code != 200:
            abort(response.status_code)
        flash("Note updated", "success")
        return redirect(url_for("notes"))
    responce = requests.get(f"{selected_service}/notes/{note_id}", headers=headers)
    if responce.status_code != 200:
        abort(responce.status_code)
    note = responce.json() 
    form.content.data = note.get("content")
    return render_template("view_note.html", form = form, title = "View Note", legend=note.get("title"), note_id = note_id)

@app.route("/remove_note/<note_id>", methods = ["GET", "POST"])
@jwt_required()
def remove_note(note_id):
    access_token = request.cookies.get('access_token_cookie')
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    selected_service = get_service_links_by_name("notes_service")
    if selected_service is None:
        abort(503)
    response = requests.delete(f"{selected_service}/notes/{note_id}", headers=headers)
    if response.status_code != 200:
        abort(response.status_code)
    flash("Note was deleted", "danger")
    return redirect(url_for("notes"))

@app.route("/note_history/<note_id>", methods = ["GET"])
@jwt_required()
def note_history(note_id):
    access_token = request.cookies.get('access_token_cookie')
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    selected_service = get_service_links_by_name("notes_service")
    if selected_service is None:
        abort(503)
    response = requests.get(f"{selected_service}/notes/{note_id}/history", headers=headers)
    if response.status_code != 200:
        abort(response.status_code)
    return render_template("notes_history.html", notes = response.json()['history'])

@app.get("/health")
def health_check():
    return "OK", 200