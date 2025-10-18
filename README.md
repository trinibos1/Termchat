# TermChat CLI Application

TermChat is a command-line interface (CLI) application that allows users to communicate with each other through a messaging service. It features user authentication, contact management, and real-time messaging with system notifications.

## Features

*   **User Authentication**: Sign up and log in securely.
*   **Contact Management**: Add and manage contacts by email.
*   **Send Messages**: Send direct messages to your contacts.
*   **View Messages**: See your message history.
*   **Update Username**: Change your display username.
*   **System Notifications**: Receive desktop notifications for new messages (requires `plyer`).
---
Please note this is still in beta
---
## Setup Instructions

### Prerequisites

*   Python 3.x
*   pip (Python package installer)

### 1. Install Dependencies

Navigate to the `messager` directory and install the required Python packages:

```bash
cd messager
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

You need to configure your Supabase credentials and a Flask secret key.

*   **`messager/message/.env`**: Create this file with your Supabase URL and Key.
    ```
        SUPABASE_URL='YOUR_SUPABASE_URL'
            SUPABASE_KEY='YOUR_SUPABASE_ANON_KEY'
                ```
                *   **`messager/api.env`**: Create this file with your Supabase URL and Key, and a Flask `SECRET_KEY`.
                    ```
                        SUPABASE_URL='YOUR_SUPABASE_URL'
                            SUPABASE_KEY='YOUR_SUPABASE_ANON_KEY'
                                SECRET_KEY='A_VERY_STRONG_SECRET_KEY_FOR_FLASK_SESSIONS'
                                    ```
                                        Replace `'YOUR_SUPABASE_URL'`, `'YOUR_SUPABASE_ANON_KEY'`, and `'A_VERY_STRONG_SECRET_KEY_FOR_FLASK_SESSIONS'` with your actual Supabase project URL, anonymous key, and a strong, unique secret key for Flask sessions, respectively.

                                        ## Running the Backend Server

                                        The backend server handles communication with Supabase and manages user sessions.

                                        1.  Open a new terminal.
                                        2.  Navigate to the `messager/message/` directory:
                                            ```bash
                                                cd messager/message/
                                                    ```
                                                    3.  Run the backend server:
                                                        ```bash
                                                            python backend.py
                                                                ```
                                                                    Leave this terminal running as long as you want to use the TermChat CLI client.

                                                                    ## Running the CLI Client

                                                                    The CLI client allows you to interact with the messaging service.

                                                                    1.  Open another new terminal.
                                                                    2.  Navigate to the `messager/message/` directory:
                                                                        ```bash
                                                                            cd messager/message/
                                                                                ```
                                                                                3.  Run the CLI client:
                                                                                    ```bash
                                                                                        python termchat.py
                                                                                            ```

                                                                                            ### Basic Usage

                                                                                            Once the client is running, you can use the following commands:

                                                                                            *   `signup`: Create a new user account.
                                                                                                *   You will be prompted for an email, password, and username.
                                                                                                *   `login`: Log in to an existing account.
                                                                                                    *   You will be prompted for your email and password.
                                                                                                    *   `add_contact`: Add a new contact by their email address.
                                                                                                    *   `send`: Send a message to one of your contacts.
                                                                                                        *   You will see a list of your contacts and choose one by number, then enter your message.
                                                                                                        *   `show`: Display your incoming and outgoing messages.
                                                                                                        *   `set_username`: Update your username.
                                                                                                        *   `help`: Show the list of available commands.
                                                                                                        *   `quit`: Exit the application.

                                                                                                        ## Running the Demo Script

                                                                                                        A demo script is provided to showcase the application's functionality by simulating two users signing up, adding each other as contacts, and exchanging messages.

                                                                                                        1.  Ensure the backend server is running as described above.
                                                                                                        2.  Open a new terminal.
                                                                                                        3.  Navigate to the `messager/` directory:
                                                                                                            ```bash
                                                                                                                cd messager/
                                                                                                                    ```
                                                                                                                    4.  Run the demo script:
                                                                                                                        ```bash
                                                                                                                            python demo.py
                                                                                                                                ```

                                                                                                                                The demo script will:
                                                                                                                                *   Install dependencies (if not already installed).
                                                                                                                                *   Guide you through setting up environment variables (though you should have done this already).
                                                                                                                                *   Prompt you to start the backend server.
                                                                                                                                *   Automatically sign up two users (`user1@example.com` and `user2@example.com`).
                                                                                                                                *   Have `user1` log in, add `user2` as a contact, and send a message.
                                                                                                                                *   Have `user2` log in, view messages, and send a reply to `user1`.

                                                                                                                                Expected output will include terminal interactions for both users, showing signup success, login messages, contact additions, and message exchanges. You will see `CLIENT STDOUT` and `CLIENT STDERR` prefixes for the output of the simulated client interactions.

                                                                                                                                ## Contributing

                                                                                                                                Feel free to fork the repository, open issues, and submit pull requests.

                                                                                                                                ## License

                                                                                                                                This project is open-source and available under the MIT License.

                                                                                                                                ## Project Information

                                                                                                                                This project was developed as a school assignment.

                                                                                                                                ### Changes Made:
                                                                                                                                * Implemented local contact storage.
                                                                                                                                * Fixed the "Could not add contact" error.
                                                                                                                                * Fixed the "Could not send message" error.
                                                                                                                                * Handled Supabase APIError exceptions in `get_messages`.
                                                                                                                                * Replaced deprecated `res.json()` with `res.model_dump_json()`.
                                                                                                                                