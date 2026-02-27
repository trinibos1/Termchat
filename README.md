

```markdown
# TermChat CLI

**TermChat** is a command-line messaging application that lets users communicate in real time.  
It includes secure authentication, contact management, direct messaging, message history, and desktop notifications for new messages (via `plyer`).

> ⚠️ **Beta version** — expect some rough edges.

## Features

- User authentication (sign up & login)
- Add and manage contacts by email
- Send direct messages to contacts
- View incoming and outgoing message history
- Change your display username
- Desktop notifications for new messages

## Requirements

- Python 3.8+
- pip

## Installation

1. Clone the repository (or extract the project folder)

2. Navigate to the project root and install dependencies:

   ```bash
   cd messager
   pip install -r requirements.txt
   ```

## Configuration

You need to create **two** `.env` files with your Supabase credentials.

### 1. Shared config (client + backend)  
Create file: `messager/message/.env`

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-or-service-key
```

### 2. Backend-only config  
Create file: `messager/api.env`

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-or-service-key
SECRET_KEY=change-this-to-a-very-long-random-string-2025
```

> **Important**: Use a strong, unique value for `SECRET_KEY` (at least 32–50 random characters).  
> You can generate one easily with: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

## Starting the Application

TermChat uses a simple backend server + interactive CLI client.

### Step 1 – Start the backend server

Open **terminal 1**:

```bash
cd messager/message
python backend.py
```

Keep this terminal running.

### Step 2 – Run the CLI client

Open **terminal 2**:

```bash
cd messager/message
python termchat.py
```

You should now see the interactive prompt and can start using commands.

## CLI Commands

Once logged in, use these commands:

| Command       | Description                                      |
|---------------|--------------------------------------------------|
| `signup`      | Create a new account                             |
| `login`       | Log in with email + password                     |
| `add_contact` | Add a contact by their email address             |
| `send`        | Send a message (select contact by number)        |
| `show`        | Display all your messages                        |
| `set_username`| Change your display name                         |
| `help`        | Show this list of commands                       |
| `quit` / `exit` | Close the application                          |

## Quick Demo (Two Simulated Users)

Watch two test users sign up, add each other, and chat:

1. Make sure the **backend server** is already running

2. In a new terminal:

   ```bash
   cd messager
   python demo.py
   ```

The script will:
- Verify/install dependencies if needed
- Remind you about `.env` files
- Create two test accounts (`user1@example.com`, `user2@example.com`)
- Log them in, add contacts, and exchange a few messages

Output is prefixed with `CLIENT STDOUT` / `CLIENT STDERR` for clarity.

## Project Status & Recent Fixes

- Implemented local contact storage
- Fixed "Could not add contact" error
- Fixed "Could not send message" error
- Improved Supabase API error handling in `get_messages`
- Replaced deprecated `res.json()` with `res.model_dump_json()`

## Contributing

Feel free to open issues, suggest improvements, or submit pull requests.

## License

MIT License

## Notes

This project was originally developed as a school assignment.

Happy chatting! 🗨️
```

