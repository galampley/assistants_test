import os
import openai
# import asyncio
import requests
import matplotlib.pyplot as plt
import time

from dotenv import load_dotenv

dotenv_path = '/Users/galampley/Documents/secrets.env'  # Replace with the path to your .env file if it's not in the current directory
load_dotenv(dotenv_path)

env_variable = os.getenv('OPENAI_API_KEY')

def list_files(assistant_id):
    # Construct the URL to list files associated with the assistant
    files_url = f"https://api.openai.com/v1/assistants/{assistant_id}/files"
    
    # Set up headers with your API key
    headers = {
        "Authorization": f"Bearer {env_variable}",
        "OpenAI-Beta": "assistants=v1",
    }
    
    try:
        # Make a GET request to retrieve the list of files
        response = requests.get(files_url, headers=headers)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            files = response.json().get("data", [])
            # Print the list of files
            print("List of files associated with the assistant:")
            for file in files:
                print(f"File ID: {file['id']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

# Define a function to display an image given its file_id
def display_image(file_id, filename=None):
    # Generate a unique filename if not provided
    if filename is None:
        timestamp = int(time.time())  # Current time in seconds since Epoch
        filename = f'image_{timestamp}.jpg'

    # Ensure the filename ends with .jpg
    if not filename.lower().endswith('.jpg'):
        filename += '.jpg'

    # Ensure directory exists for filename, adjust if you're saving in a specific folder
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    try:
        # Attempt to retrieve and read the file content
        content = openai.files.content(file_id).read()
    except Exception as e:
        print(f"An error occurred while retrieving the file: {e}")
        return None  # Return None to indicate the image was not retrieved

    try:
        # Attempt to open a file in binary write mode and write the content to it
        full_path = os.path.join(directory, filename)
        with open(full_path, 'wb') as f:
            f.write(content)
        print(f"The image has been saved successfully as {filename}!")
        return full_path  # Return the path to the saved image
    except IOError as e:  # Catch filesystem-related errors
        print(f"An error occurred while writing the file: {e}")
        return None
    except Exception as e:  # Catch any other unforeseen errors
        print(f"An unexpected error occurred: {e}")
        return None

def fetch_and_display_run_steps(thread_id, run_id):
    # Construct the API endpoint URL
    url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}/steps"

    # Set up headers with your API key
    headers = {
            "Authorization": f"Bearer {env_variable}",
            "OpenAI-Beta": "assistants=v1",
        }

    try:
        # Make the GET request to fetch run steps
        response = requests.get(url, headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            run_steps = response.json()

            print("Run Steps:")
            for step in run_steps["data"]:
                print(step)
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except Exception as error:
        print(error)


def get_query(query):
    return input(query)

def main():
    try:
        '''
        file_csv = openai.files.create(
            file=open("context/StudentsPerformance.csv", "rb"),
            purpose='assistants'
        )
        
        file_txt = openai.files.create(
            file=open("context/math_essay.txt", "rb"),
            purpose='assistants'
        )
        '''

        with open("context/StudentsPerformance.csv", "rb") as file_handle_csv:
            file_csv = openai.files.create(
                file=file_handle_csv,
                purpose='assistants'
            )

        with open("context/math_essay.txt", "rb") as file_handle_txt:
            file_txt = openai.files.create(
                file=file_handle_txt,
                purpose='assistants'
            )
        # Create a new assistant
        assistant = openai.beta.assistants.create(
            name="Math Tutor",
            instructions="You are a personal math tutor. You have access to math essay documentation. You also write and run code to answer math questions. Also create data visualizations where requested.\
            You can analyze data present in .csv files, understand trends, and come up with data visualizations relevant to those trends.\
            You also share a brief text summary of the trends observed.",
            tools=[{"type":"code_interpreter"}, {"type": "retrieval"}],
            model="gpt-4-1106-preview",
            file_ids=[file_csv.id, file_txt.id]
        )

        print("\nHello there, I'm your personal math tutor. Ask some complicated questions.\n")

        # Create a thread
        thread = openai.beta.threads.create()

        # Use keep_asking as state to keep asking questions
        keep_asking = True
        while keep_asking:
            user_query = get_query("\nUser: ")

            # Pass in the user question into the existing thread
            openai.beta.threads.messages.create(
                role="user",
                content=user_query,
                thread_id=thread.id
            )

            # Use runs to wait for the assistant response and then retrieve it
            run = openai.beta.threads.runs.create(
                assistant_id=assistant.id,
                thread_id=thread.id
            )

            # Polling mechanism to see if run_status is completed
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

            while run_status.status != "completed":
                run_status = openai.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

            run_steps = fetch_and_display_run_steps(thread.id, run.id)
            run_steps

            # Get the last assistant message from the messages array
            messages = openai.beta.threads.messages.list(thread_id=thread.id)

            response_list = []
            
            for message in messages:  
                if message.role == 'assistant' and message.run_id == run.id:
                    for content in message.content:
                        if content.type == 'text':
                            assistant_response = content.text.value
                            response_list.append(assistant_response)  # Append each value to the list
                        if content.type == 'image_file':
                            assistant_img = content.image_file.file_id
                            display_image(assistant_img)
                
            # Reverse the collected list once after all responses are collected
            response_list.reverse()

            # Print the reversed list as a string
            for response in response_list:
                print(response)  # Print each response from the list
            
    except Exception as error:
        print(error)

if __name__ == "__main__":
    main()