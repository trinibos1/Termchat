#!/usr/bin/env python3
import getpass
import os
import logging
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import re
import requests

session_cookies = None # Global variable to store session cookies

logging.basicConfig(level=logging.WARNING)
console = Console()

# ===== User Messages (Variables) =====

welcome_text = "Welcome to TermChat CLI!"
login_required_msg = "[bold red]⚠ You must login first to use this command.[/bold red]"
signup_success_msg = "[green]✅ Signup successful! Please login now.[/green]"
message_sent_msg = "[green]📤 Message sent![/green]"
unknown_command_msg = "[yellow]❓ Unknown command. Type 'help' to see available commands.[/yellow]"
goodbye_msg = "[cyan]👋 Goodbye![/cyan]"
no_contacts_msg = "[bold yellow]⚠ No contacts found. Add some first.[/bold yellow]"
invalid_email_msg = "[red]❌ Invalid email format.[/red]"


# ===== Functions =====

def input_email():
    while True:
        email = Prompt.ask("Email")
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return email
        console.print(invalid_email_msg)


def signup():
    console.rule("[bold blue]Sign Up[/bold blue]")
    try:
        email = input_email()
        password = getpass.getpass("Password: ")
        username = Prompt.ask("Choose a username")
        response = requests.post("http://127.0.0.1:5000/signup", json={"email": email, "password": password, "username": username})
        if response.status_code == 200:
            console.print(signup_success_msg)
            return None
        else:
            error_message = response.json().get("message", "Unknown error during signup.")
            logging.error(f"Signup error: {error_message}")
            console.print(f"[red]Error: {error_message}[/red]")
            return None
    except Exception:
        console.print(f"[red]⚠ Signup failed. Please check your connection and try again.[/red]")
        return None

def login():
    console.rule("[bold blue]Login[/bold blue]")
    try:
        email = input_email()
        password = getpass.getpass("Password: ")
        global session_cookies
        response = requests.post("http://127.0.0.1:5000/login", json={"email": email, "password": password})
        if response.status_code == 200:
            session_cookies = response.cookies # Store session cookies
            user_data = response.json()
            class User:
                def __init__(self, id):
                    self.id = id
            current_user = User(user_data["user_id"])
            
            profile_response = requests.get(f"http://127.0.0.1:5000/get_profile/{current_user.id}", cookies=session_cookies)
            profile = profile_response.json() if profile_response.status_code == 200 else None

        else:
            error_message = response.json().get("message", "Unknown error during login.")
            logging.error(f"Login error: {error_message}")
            console.print(f"[red]Error: {error_message}[/red]")
            return None
    except Exception:
        console.print(f"[red]⚠ Login failed. Please check your connection and try again.[/red]")
        return None
    if profile and 'username' in profile:
        welcome_back_msg = f"[bold green]👋 Welcome back, [cyan]{profile['username']}[/cyan]![/bold green]"
        console.print(Panel(welcome_back_msg, expand=False, border_style="green"))
    else:
        console.print(Panel("[bold green]👋 Welcome back! (Profile username not found)[/bold green]", expand=False, border_style="green"))
    return current_user


def add_contact(current_user):
    global session_cookies
    try:
        email = Prompt.ask("Enter contact's email")
        response = requests.post("http://127.0.0.1:5000/add_contact", json={"contact_email": email}, cookies=session_cookies)
        if response.status_code == 200:
            console.print("[green]✅ Contact added.[/green]")
        else:
            error_message = response.json().get("message", "Unknown error during adding contact.")
            logging.error(f"Add contact error: {error_message}")
            console.print(f"[red]Error: {error_message}[/red]")
    except Exception:
        console.print(f"[red]⚠ Could not add contact. Please check your connection and try again.[/red]")


def send_message(current_user):
    global session_cookies
    try:
        response = requests.get("http://127.0.0.1:5000/get_contacts", cookies=session_cookies)
        if response.status_code == 200:
            contacts = response.json().get("contacts", [])
            if not contacts:
                console.print(no_contacts_msg)
                return
            console.print("[bold]Your Contacts:[/bold]")
            for i, c in enumerate(contacts, start=1):
                console.print(f" {i}. [cyan]{c['username']}[/cyan] ({c['email']})")
            choice = Prompt.ask("Send message to (number)")
            if not choice.isdigit() or not (1 <= int(choice) <= len(contacts)):
                console.print("[red]Invalid choice.[/red]")
                return
            contact = contacts[int(choice) - 1]
            content = Prompt.ask("Enter message")
            try:
                send_response = requests.post("http://127.0.0.1:5000/send_message", json={"receiver_email": contact["email"], "content": content}, cookies=session_cookies)
                if send_response.status_code == 200:
                    console.print(message_sent_msg)
                else:
                    error_message = send_response.json().get("message", "Unknown error during sending message.")
                    logging.error(f"Send message error: {error_message}")
                    console.print(f"[red]Error: {error_message}[/red]")
            except Exception as e:
                console.print(f"[red]⚠ Could not send message. Please check your connection and try again. {e}[/red]")
        else:
            error_message = response.json().get("message", "Unknown error during retrieving contacts.")
            logging.error(f"Get contacts error: {error_message}")
            console.print(f"[red]Error: {error_message}[/red]")
    except Exception as e:
        console.print(f"[red]⚠ Could not send message. Please check your connection and try again. {e}[/red]")

def show_messages(current_user):
    global session_cookies
    try:
        response = requests.get("http://127.0.0.1:5000/show_messages", cookies=session_cookies)
        if response.status_code == 200:
            messages = response.json().get("messages", [])
            if not messages:
                console.print("[dim]No messages.[/dim]")
                return
            console.rule("[bold magenta]📨 Your Messages[/bold magenta]")
            for msg in messages:
                sender_id = msg["sender_id"]
                receiver_id = msg["receiver_id"]
                content = msg["content"]
                created_at = msg["created_at"]

                direction = "->" if sender_id == current_user.id else "<-"
                console.print(
                    f"[dim]{created_at}[/dim] [cyan]{sender_id[:8]}...[/cyan] {direction} [magenta]{receiver_id[:8]}...[/magenta]: {content}"
                )
        else:
            error_message = response.json().get("message", "Unknown error during showing messages.")
            logging.error(f"Show messages error: {error_message}")
            console.print(f"[red]Error: {error_message}[/red]")
    except Exception:
        console.print(f"[red]⚠ Could not show messages. Please check your connection and try again.[/red]")


def help_menu():
    console.rule("[bold blue]Help Menu[/bold blue]")
    console.print(
        """
        [bold yellow]Commands:[/bold yellow]
        [green] signup[/green]       - Create a new account
        [green] login[/green]        - Login with email and password
        [green] add_contact[/green]  - Add a contact by email
        [green] send[/green]         - Send a message to a contact
        [green] show[/green]         - Show your messages
        [green] help[/green]         - Show this menu
        [green] set_username[/green] - Set or update your username
        [green] quit[/green]         - Exit the app
        """
    )

def set_username(current_user):
    global session_cookies
    try:
        new_username = Prompt.ask("Enter new username")
        response = requests.post("http://127.0.0.1:5000/set_username", json={"username": new_username}, cookies=session_cookies)
        if response.status_code == 200:
            console.print(f"[green]✅ Username updated to [cyan]{new_username}[/cyan].[/green]")
        else:
            error_message = response.json().get("message", "Unknown error during updating username.")
            logging.error(f"Update username error: {error_message}")
            console.print(f"[red]Error: {error_message}[/red]")
    except Exception:
        console.print(f"[red]⚠ Failed to update username. Please try again.[/red]")

def main():
    try:
        import os
        os.environ["SUPABASE_LOGGING_ENABLED"] = "False"
        load_dotenv()
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("hpack").setLevel(logging.WARNING)

        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")

        if not SUPABASE_URL or not SUPABASE_KEY:
            logging.error("Missing Supabase configuration")
            console.print("[red]⚠ Connection error: Service unavailable[/red]")
            return

        console.print("[green]✅ Connected to the messaging service.[/green]")

        current_user = None # This will now store a simplified user object with just the ID

        console.rule("[bold green]" + welcome_text + "[/bold green]")
        help_menu()

        while True:
            try:
                cmd = Prompt.ask("\n[bold blue]>[/bold blue]").strip().lower()
            except Exception as e:
                logging.exception("Error reading input")
                console.print(f"[red]⚠ An error occurred while reading your input. See logs for details.[/red]")
                continue
            if cmd == "signup":
                signup()
            elif cmd == "login":
                current_user = login()
            elif cmd == "add_contact":
                if not current_user:
                    console.print(login_required_msg)
                    continue
                add_contact(current_user)
            elif cmd == "send":
                if not current_user:
                    console.print(login_required_msg)
                    continue
                send_message(current_user)
            elif cmd == "show":
                if not current_user:
                    console.print(login_required_msg)
                    continue
                show_messages(current_user)
            elif cmd == "help":
                help_menu()
            elif cmd == "set_username":
                if not current_user:
                    console.print(login_required_msg)
                    continue
                set_username(current_user)
            elif cmd == "quit":
                console.print(goodbye_msg)
                break
            else:
                console.print(unknown_command_msg)

    except Exception as e:
        logging.exception("An unexpected error occurred in main")
        console.print(f"[red]⚠ An unexpected error occurred in main. See logs for details.[/red]")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]⚠ An unexpected error occurred in main: {e}. The application will now exit.[/red]")
