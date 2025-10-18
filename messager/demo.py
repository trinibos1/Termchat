import os
import subprocess
import time
import sys
import threading

def run_command(command, cwd=None, shell=True, input_data=None):
    """Helper to run shell commands and print their output."""
    print(f"\nExecuting: {command}")
    process = subprocess.Popen(
        command,
        cwd=cwd,
        shell=shell,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    if input_data:
        for line in input_data:
            process.stdin.write(line + '\n')
            process.stdin.flush()
            time.sleep(0.5) # Give some time for the client to process input

    stdout_output = []
    stderr_output = []

    def read_stdout():
        for line in process.stdout:
            print(f"CLIENT STDOUT: {line.strip()}")
            stdout_output.append(line)

    def read_stderr():
        for line in process.stderr:
            print(f"CLIENT STDERR: {line.strip()}")
            stderr_output.append(line)

    stdout_thread = threading.Thread(target=read_stdout)
    stderr_thread = threading.Thread(target=read_stderr)

    stdout_thread.start()
    stderr_thread.start()

    process.wait()
    stdout_thread.join()
    stderr_thread.join()

    return process.returncode, "".join(stdout_output), "".join(stderr_output)

def main():
    print("========================================")
    print("       TermChat CLI Application Demo    ")
    print("========================================")
    print("\nThis demo will guide you through setting up and interacting with the TermChat application.")
    print("It assumes you have Python 3 and pip installed.")

    # Step 1: Install dependencies
    print("\n--- Step 1: Installing Python dependencies ---")
    print("Please ensure you are in the 'messager' directory for this step.")
    input("Press Enter to continue...")
    run_command("pip install -r requirements.txt", cwd="messager")

    # Step 2: Environment variables setup
    print("\n--- Step 2: Setting up environment variables ---")
    print("You need to create a '.env' file in 'messager/message/' and 'api.env' in 'messager/'")
    print("These files should contain your Supabase URL and Key, and a SECRET_KEY for Flask session.")
    print("Example .env content:")
    print("SUPABASE_URL='YOUR_SUPABASE_URL'")
    print("SUPABASE_KEY='YOUR_SUPABASE_ANON_KEY'")
    print("SECRET_KEY='A_VERY_SECRET_KEY'")
    input("Press Enter after setting up your .env files...")

    # Step 3: Start the backend server
    print("\n--- Step 3: Starting the backend server ---")
    print("The backend server (backend.py) needs to run in a separate terminal.")
    print("Please open a NEW terminal, navigate to 'messager/message/', and run:")
    print("python backend.py")
    print("Leave this terminal running for the duration of the demo.")
    input("Press Enter once the backend server is running in a separate terminal...")

    # Step 4: Automated interaction with TermChat client (User 1)
    print("\n--- Step 4: Automated interaction with TermChat client (User 1) ---")
    print("We will now simulate user1's interactions with the termchat client.")

    user1_email = "user1@example.com"
    user1_password = "password123"
    user1_username = "userone"

    user2_email = "user2@example.com"
    user2_password = "password123"
    user2_username = "usertwo"

    # Signup User 1
    print(f"\n--- User 1: Signing up {user1_username} ---")
    run_command(
        "python termchat.py",
        cwd="messager/message",
        input_data=[
            "signup",
            user1_email,
            user1_password,
            user1_username,
            "quit"
        ]
    )
    time.sleep(2) # Give backend time to process

    # Signup User 2
    print(f"\n--- User 2: Signing up {user2_username} ---")
    run_command(
        "python termchat.py",
        cwd="messager/message",
        input_data=[
            "signup",
            user2_email,
            user2_password,
            user2_username,
            "quit"
        ]
    )
    time.sleep(2) # Give backend time to process

    # User 1 logs in, adds contact, sends message
    print(f"\n--- User 1: Logging in, adding {user2_username} as contact, and sending message ---")
    run_command(
        "python termchat.py",
        cwd="messager/message",
        input_data=[
            "login",
            user1_email,
            user1_password,
            "add_contact",
            user2_email,
            "send",
            "1", # Assuming user2 is the first contact
            "Hello from user1!",
            "quit"
        ]
    )
    time.sleep(2) # Give backend time to process

    # User 2 logs in, shows messages, sends message back
    print(f"\n--- User 2: Logging in, showing messages, and sending message back to {user1_username} ---")
    run_command(
        "python termchat.py",
        cwd="messager/message",
        input_data=[
            "login",
            user2_email,
            user2_password,
            "show",
            "send",
            "1", # Assuming user1 is the first contact
            "Hi user1, got your message!",
            "quit"
        ]
    )
    time.sleep(2) # Give backend time to process

    print("\n========================================")
    print("       Demo Complete!                   ")
    print("========================================")
    print("You have successfully demonstrated the TermChat CLI application.")
    print("Remember to stop the backend server running in the other terminal.")

if __name__ == "__main__":
    main()