import os
import time
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from plyer import notification
from flask import Flask, session, request, jsonify
from flask_session import Session
from functools import wraps

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.INFO)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY") or "supersecretkey"  # Use a strong secret key in production
server_session = Session(app)

logging.info("Starting the Flask app")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return jsonify({"message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

class Backend:
    def __init__(self, jwt_token=None):
        logging.info("Initializing Supabase client...")
        options = None
        if jwt_token:
            from supabase import ClientOptions
            options = ClientOptions(headers={"Authorization": f"Bearer {jwt_token}"})
            self.supabase: Client = create_client(
                os.environ.get("SUPABASE_URL"),
                os.environ.get("SUPABASE_KEY"),
                options=options
            )
            logging.info("Supabase client initialized with JWT token.")
        else:
            self.supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
            logging.info("Supabase client initialized with anon key.")

        if self.supabase:
            logging.info("Supabase client initialized successfully.")
        else:
            logging.error("Failed to initialize Supabase client.")
        self.last_message_id = None

    def update_username(self, user_id: str, new_username: str):
        res = self.supabase.table("profiles").update({"username": new_username}).eq("id", user_id).execute()
        if res.error:
            logging.error(f"Update username error: {res.error}")
            return False, "Failed to update username."
        return True, None


    def signup(self, email: str, password: str, username: str):
        if not isinstance(email, str) or "@" not in email:
            return None, "Invalid email format"
        if not isinstance(password, str) or len(password) < 8:
            return None, "Password must be at least 8 characters"

        user = self.supabase.auth.sign_up({"email": email, "password": password})
        if user and user.user is None:
            logging.error(f"Signup failed: {user.error}")
            return None, "Signup failed. Please try again later."
        user_id = user.user.id

        logging.info(f"Signup attempt with email: {email}, username: {username}")
        data, error = self.supabase.table("profiles").insert({
            "id": user_id,
            "email": email,
            "username": username
        }).execute()
        if error:
            logging.error(f"Signup error: {error}")
            return None, "Signup failed. Please try again later."
        return user.user, None

    def login(self, email: str, password: str):
        response = self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user is None:
            logging.error("Login failed")
            return None, "Login failed. Please try again."
        return response.user, response.session.access_token, None
    def get_profile(self, user_id: str):
        logging.debug(f"get_profile: Attempting to fetch profile for user_id: '{user_id}' (type: {type(user_id)})")
        
        # First, try to get the user from auth.users to ensure we have the correct ID
        try:
            user_response = self.supabase.auth.get_user()
            if user_response and user_response.user and user_response.user.id == user_id:
                logging.debug(f"get_profile: Authenticated user ID matches requested user_id: {user_id}")
            else:
                logging.warning(f"get_profile: Authenticated user ID does not match requested user_id or user not found via auth.get_user().")
                # If the user_id doesn't match the currently authenticated user, we might still want to fetch it
                # but it's important to note this discrepancy.
        except Exception as e:
            logging.error(f"get_profile: Error fetching authenticated user: {e}")
            # Continue with the direct profile query even if auth.get_user fails

        res = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
        logging.debug(f"get_profile: Supabase response (res): {res}")
        logging.debug(f"get_profile: Supabase response data (res.data): {res.data}")
        if res.data:
            if isinstance(res.data, list) and len(res.data) > 0:
                logging.debug(f"get_profile: Profile found for user_id: {user_id}")
                return res.data[0]
            else:
                logging.warning(f"get_profile: res.data is not a non-empty list for user_id: {user_id}")
        logging.warning(f"get_profile: No profile found for user_id: {user_id}")
        return None

    def get_profile_by_email(self, email: str):
        res = self.supabase.table("profiles").select("*").eq("email", email).execute()
        if res.data:
            return res.data[0]
        return None

    def add_contact(self, owner_id: str, contact_email: str):
        import json
        contacts_file = "contacts.json"
        logging.info(f"add_contact: Adding contact {contact_email} for owner {owner_id}")
        contact = self.get_profile_by_email(contact_email)
        if not contact:
            logging.warning(f"add_contact: Contact {contact_email} not found")
            return False, "Contact not found"

        # Load existing contacts from file
        try:
            with open(contacts_file, "r") as f:
                contacts = json.load(f)
        except FileNotFoundError:
            contacts = []
        except json.JSONDecodeError:
            logging.error("Could not decode contacts.json, starting with empty list")
            contacts = []

        # Check if contact already exists
        for c in contacts:
            if c["owner_id"] == owner_id and c["contact_email"] == contact_email:
                return False, "Contact already added locally"

        # Add contact to local list
        contacts.append({"owner_id": "default_owner_id", "contact_email": "trinibos1@proton.me"})

        # Write updated contacts to file
        with open(contacts_file, "w") as f:
            json.dump(contacts, f)

        try:
            logging.info(f"add_contact: Attempting to add contact to database")
            res = self.supabase.table("contacts").insert({
                "owner_id": owner_id,
                "contact_id": contact["id"]
            }).execute()
            logging.info(f"add_contact: Contact added to database successfully")
        except Exception as e:
            logging.error(f"add_contact: Error adding contact: {e}")
            return False, "Failed to add contact."

        if res.status_code != 201 or res.data is None:
            logging.error(f"add_contact: Supabase error: {res.status_code} - {res.data}")
            return False, "Failed to add contact."
        logging.info(f"add_contact: Contact {contact_email} added successfully for owner {owner_id}")
        return True, None

    def get_contacts(self, owner_id: str):
        res = self.supabase.table("contacts").select("contact_id").eq("owner_id", owner_id).execute()
        if not res.data:
            return []
        contacts = []
        for c in res.data:
            p = self.get_profile(c["contact_id"])
            if p:
                contacts.append(p)
        return contacts

    def delete_contact(self, owner_id: str, contact_email: str):
        """
        Deletes a contact from the user's contact list.
        """
        try:
            contact = self.get_profile_by_email(contact_email)
            if not contact:
                logging.warning(f"delete_contact: Contact with email {contact_email} not found for user {owner_id}")
                return False, "Contact not found"

            res = self.supabase.table("contacts").delete()\
                .eq("owner_id", owner_id).eq("contact_id", contact["id"]).execute()

            if res.error:
                logging.error(f"Delete contact error: {res.error}")
                return False, "Failed to delete contact."
            logging.info(f"delete_contact: Contact {contact_email} deleted for user {owner_id}")
            return True, "Contact deleted successfully"
        except Exception as e:
            logging.error(f"delete_contact: Error deleting contact {contact_email} for user {owner_id}: {e}")
            return False, str(e)

    def send_message(self, sender_id: str, receiver_email: str, content: str):
        receiver = self.get_profile_by_email(receiver_email)
        if not receiver:
            return False, "Receiver not found"

        print(f"Attempting to send message from {sender_id} to {receiver_email}")
        try:
            try:
                print(f"Sending message content: {content}")
                print(f"Receiver: {receiver}")
                res = self.supabase.table("messages").insert({
                    "sender_id": sender_id,
                    "receiver_id": receiver["id"],
                    "content": content
                }).execute()
                print("Message sent successfully")
                print(f"Supabase response: {res}")
            except Exception as e:
                logging.error(f"Send message error: {e}")
                print(f"Error during message sending: {e}")
                return False, "Failed to send message."
        except Exception as e:
            logging.error(f"Send message error: {e}")
            print(f"Outer error during message sending: {e}")
            return False, "Failed to send message."

        logging.info(f"Supabase response object: {res}")
        logging.info(f"Supabase response type: {type(res)}")
        if hasattr(res, 'status_code'):
            logging.info(f"Supabase response status_code: {res.status_code}")
        else:
            logging.info("Supabase response does not have status_code attribute")
        if hasattr(res, 'data'):
            logging.info(f"Supabase response data: {res.data}")
        else:
            logging.info("Supabase response does not have data attribute")

        if hasattr(res, 'error'):
            logging.info(f"Supabase response error: {res.error}")
        else:
            logging.info("Supabase response does not have error attribute")

        if hasattr(res, 'status_code'):
            logging.info(f"Supabase response status_code: {res.status_code}")
        else:
            logging.info("Supabase response does not have status_code attribute")

        if hasattr(res, 'data'):
            logging.info(f"Supabase response data: {res.data}")
        else:
            logging.info("Supabase response does not have data attribute")

        if res and hasattr(res, 'model_dump_json'):
            try:
                res_json = res.model_dump_json()
                logging.info(f"Supabase response json: {res_json}")
            except Exception as e:
                logging.error(f"Could not parse res.model_dump_json(): {e}")
        else:
            logging.info("Supabase response does not have json attribute or is None")

        if res and hasattr(res, 'status_code') and res.status_code >= 400:
            logging.error(f"Send message error: Status code indicates failure: {res.status_code}")
            print(f"Supabase error: Status code indicates failure: {res.status_code}")
            raise Exception("Could not send message")

        if not res or not hasattr(res, 'data') or not res.data:
            logging.error(f"Send message error: No data returned")
            print(f"Supabase error: No data returned")
            raise Exception("Could not send message")
        return True, None

    def get_messages(self, user_id: str):
        try:
            res = self.supabase.table("messages")\
                .select("id, sender_id, receiver_id, content, created_at")\
                .or_(f"sender_id.eq.{user_id},receiver_id.eq.{user_id}")\
                .order("created_at", desc=False)\
                .execute()
        except Exception as e:
            logging.exception(f"Get messages error: {e}")
            return []

        logging.info(f"get_messages: Supabase response (res): {res}")
        logging.info(f"get_messages: Supabase response type: {type(res)}")

        if hasattr(res, 'error'):
            logging.info(f"get_messages: Supabase response error: {res.error}")
        else:
            logging.info("get_messages: Supabase response does not have error attribute")

        if hasattr(res, 'data'):
            logging.info(f"get_messages: Supabase response data: {res.data}")
        else:
            logging.info("get_messages: Supabase response does not have data attribute")

        if hasattr(res, 'status_code'):
            logging.info(f"get_messages: Supabase response status_code: {res.status_code}")
        else:
            logging.info("get_messages: Supabase response does not have status_code attribute")

        if res and hasattr(res, 'model_dump_json'):
            try:
                res_json = res.model_dump_json()
                logging.info(f"get_messages: Supabase response json: {res_json}")
            except Exception as e:
                logging.error(f"Could not parse res.model_dump_json(): {e}")
        else:
            logging.info("get_messages: Supabase response does not have json attribute or is None")

        if res is None:
            logging.error("Get messages error: Response is None")
            return []

        if hasattr(res, 'status_code') and res.status_code >= 400:
            logging.error(f"Get messages error: HTTP status code indicates failure: {res.status_code}")
            return []

        if not hasattr(res, 'data') or res.data is None or len(res.data) == 0:
            logging.error("Get messages error: No data returned from Supabase")
            return []

        return res.data

    def poll_messages(self, user_id: str, interval=5):
        """
        Polls for new messages in the background and sends system notifications.
        """
        print("[Listening for new messages every", interval, "seconds...]")
        while True:
            messages = self.get_messages(user_id)
            if not messages:
                time.sleep(interval)
                continue

            latest = messages[-1]
            if self.last_message_id != latest["id"] and latest["receiver_id"] == user_id:
                sender = self.get_profile(latest["sender_id"])
                sender_name = sender["username"] if sender else "Unknown"
                content = latest["content"]
                notification.notify(
                    title=f"📨 New message from {sender_name}",
                    message=content,
                    timeout=5  # seconds
                )
                self.last_message_id = latest["id"]

            time.sleep(interval)

@app.route("/logout")
@login_required
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out"}), 200

@app.route("/signup", methods=["POST"])
def signup_route():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    if not all([email, password, username]):
        return jsonify({"message": "Missing email, password, or username"}), 400

    backend = Backend()
    user, error = backend.signup(email, password, username)
    if error:
        return jsonify({"message": error}), 400
    
    session['user_id'] = user.id
    return jsonify({"message": "Signup successful", "user_id": user.id}), 200

@app.route("/login", methods=["POST"])
def login_route():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"message": "Missing email or password"}), 400

    backend = Backend()
    user, jwt_token, error = backend.login(email, password)
    if error:
        return jsonify({"message": error}), 401
    
    session['user_id'] = user.id
    session['jwt_token'] = jwt_token
    return jsonify({"message": "Login successful", "user_id": user.id}), 200

@app.route("/get_profile/<user_id>", methods=["GET"])
@login_required
def get_profile_route(user_id):
    jwt_token = session.get('jwt_token')
    backend = Backend(jwt_token)
    profile = backend.get_profile(user_id)
    if profile:
        return jsonify(profile), 200
    return jsonify({"message": "Profile not found"}), 404

@app.route("/add_contact", methods=["POST"])
@login_required
def add_contact_route():
    data = request.json
    contact_email = data.get("contact_email")
    user_id = session.get('user_id')

    if not contact_email:
        return jsonify({"message": "Missing contact email"}), 400

    jwt_token = session.get('jwt_token')
    backend = Backend(jwt_token)
    success, message = backend.add_contact(user_id, contact_email)
    if not success:
        return jsonify({"message": message}), 400
    return jsonify({"message": "Contact added successfully"}), 200

@app.route("/get_contacts", methods=["GET"])
@login_required
def get_contacts_route():
    user_id = session.get('user_id')
    jwt_token = session.get('jwt_token')
    backend = Backend(jwt_token)
    contacts = backend.get_contacts(user_id)
    if contacts is None:
        return jsonify({"message": "Failed to retrieve contacts"}), 500
    return jsonify({"contacts": contacts}), 200

@app.route("/send_message", methods=["POST"])
@login_required
def send_message_route():
    data = request.get_json()
    receiver_email = data.get("receiver_email")
    content = data.get("content")
    sender_id = session.get('user_id')

    if not all([receiver_email, content]):
        return jsonify({"message": "Missing receiver email or content"}), 400

    jwt_token = session.get('jwt_token')
    backend = Backend(jwt_token)
    success, message = backend.send_message(sender_id, receiver_email, content)
    if not success:
        return jsonify({"message": message}), 400
    return jsonify({"message": "Message sent successfully"}), 200

@app.route("/show_messages", methods=["GET"])
@login_required
def show_messages_route():
    user_id = session.get('user_id')
    jwt_token = session.get('jwt_token')
    backend = Backend(jwt_token)
    messages = backend.get_messages(user_id)
    if messages is None:
        return jsonify({"message": "Failed to retrieve messages"}), 500
    return jsonify({"messages": messages}), 200

@app.route("/set_username", methods=["POST"])
@login_required
def set_username_route():
    data = request.json
    new_username = data.get("username")
    user_id = session.get('user_id')

    if not new_username:
        return jsonify({"message": "Missing username"}), 400

    jwt_token = session.get('jwt_token')
    backend = Backend(jwt_token)
    success, message = backend.update_username(user_id, new_username)
    if not success:
        return jsonify({"message": message}), 400
    return jsonify({"message": "Username updated successfully"}), 200


if __name__ == '__main__':
    try:
        logging.info("Running the app in debug mode")
        app.run(debug=True)
    except Exception as e:
        logging.exception("App crashed during startup")

