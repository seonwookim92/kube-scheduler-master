import threading
import time

# Define your background function here
def background_function():
    # Do some work here
    for i in range(10):
        print("Background function is working...")
        time.sleep(1)

# Define a function to handle user input
def handle_user_input():
    while True:
        # Get user input here
        user_input = input("Enter your input: ")
        # Process user input here
        print("You entered:", user_input)

# Create a new thread for your background function
with open('background.log', 'w') as f:
    background_thread = threading.Thread(target=background_function, stdout=f)
    background_thread.start()

# Call your function to handle user input
handle_user_input()
