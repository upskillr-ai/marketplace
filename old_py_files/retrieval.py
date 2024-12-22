from openai import OpenAI
import os
import tiktoken
import openai
import time
from pprint import pprint
from bs4 import BeautifulSoup
import requests, time, shutil, threading, tempfile
from youtube_transcript_api import YouTubeTranscriptApi
import re, serpapi, json
from pydub import AudioSegment
import googleapiclient.discovery


SERP_API = "49ac6a36f7f17c2f5e99e0b18b80cc768348a2d56238748555bb6382bf203c69"
INPUT_CSE_ID = "e4b6b224faa9941d0"
GOOGLE_INSTRUCTIONS = " Further, as a Google Search assistant, your task is to fetch and display the latest information from web browsing based on user queries if and only if you cannot find any relevant information from the resources provided by the user. You should be able to accurately and efficiently retrieve relevant and up-to-date information from the internet in response to user queries. Your response should prioritize the use of provided resources for information, and only resort to web browsing when necessary. When web browsing is required, your response should focus on retrieving the most recent and relevant information available. Your retrieval process should be accurate, efficient, and tailored to the user's query. Your first initial response should include a warm welcome, and if the user says 'Hello', always reply back with 'Hello, how may I help you today?' and 1-2 lines about yourself"

GET_ORGANIC_RESULTS_JSON = {
  "name": "get_organic_results",
  "description": "Fetch real time web answers based on a search query",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "num_results": {
        "type": "integer",
        "description": "Number of results to return"
      }
    },
    "required": ["query"]
  }
}


KEY_SETS = [
    {"api_key": "AIzaSyDRZCLORdurcmxB0sqQZ3esOy-JcwnngQQ", "cse_id": "043e1dbeb68b147f8"},
    {"api_key": "AIzaSyCQjbfF8FNvx8NqrVsOWx7w2Yb7eGfH4YM", "cse_id": "b1b5a36e9e0c24a88"},
    {"api_key": "AIzaSyCSyNQj2hThfAMuaNxOdOTybaGQrDPzS3A", "cse_id": "8612e19203c034bdd"},
    {"api_key": "AIzaSyDWW3XWKcKXmE65-XKqMAtkxHS8hyCN2vk", "cse_id": "e0acad44d64994b9b"},
    {"api_key": "AIzaSyAvwsXNHFkDUMcUjKJLBDJ4iDtIZQOGydU", "cse_id": "73f85d9469df946d6"},
    {"api_key": "AIzaSyD34mGAOX735JxW6jeGdyPvvKcV-L6wzrM", "cse_id": "8343b22108a944d96"},
    {"api_key": "AIzaSyA264rlmwE2d0chFnx5UxNOTDS4h3rfYY4", "cse_id": "a1326204d45424ac0"},
    {"api_key": "AIzaSyBk5b44tZxdwNIoZ16AKPgSa6OV6lnh8PQ", "cse_id": "958fa6a45e6414ef2"},
    {"api_key": "AIzaSyCpbpDKkHyvGigVx4ntz3FrRf9qwXbSH3U", "cse_id": "f10739637d96048c6"},
    {"api_key": "AIzaSyBNPF9xlzATBw36px9jkioYukKDnJ3nb7M", "cse_id": "7782535469acf4e2e"},
    {"api_key": "AIzaSyAyo4s8WpWQIlrjCIxnzp0zh1Iw6M_2QlQ", "cse_id": "30ba44e27195f4d8b"},
    {"api_key": "AIzaSyBeKLcrkGSKTdPFlp0uxtwEBZtuIGokfcs", "cse_id": "348047a91ff9440a7"},
    {"api_key": "AIzaSyAfegpggIqI0m3yawi61F6dyzE9CjqGcTQ", "cse_id": "76d90d70e38e94689"},
    {"api_key": "AIzaSyB9HCWkqRTs9DOLBqoJndNjIT-sSMUtwDM", "cse_id": "34757d337562647fa"},
    {"api_key": "AIzaSyASIZSXbtuZZD1XEBXS79sQsJx8RkbdURU", "cse_id": "d024e8d32a8a94c3f"},
    {"api_key": "AIzaSyD2UvWCndRQ07RXN73EplGR99FPzAZvK64", "cse_id": "0795f779e268c424b"},
    {"api_key": "AIzaSyDelMZsMGxb6hC8bLVMrFgBsGvNrHxjFiA", "cse_id": "349d7551e3b644f75"},
    {"api_key": "AIzaSyCGDsPwhAPe6pmufdU6Vd4CGqjj_-TT7DY", "cse_id": "7483f9d9ef67d48da"},
    {"api_key": "AIzaSyC1CWAhxdDw6dPCvuCazU5e93O2lw1oWKg", "cse_id": "0414abcb763a74c27"},
    {"api_key": "AIzaSyDS_N6pK-auDfLdRNr5AZb08RB_3tiM7jM", "cse_id": "a4cb4deceefac447b"},
    {"api_key": "AIzaSyBLY9IEOcZKzvY95hegYOPwBACB6lCplrU", "cse_id": "e4b6b224faa9941d0"}
]


api_service_name, api_version, current_key_index = "youtube", "v3", 0
current_youtube_key_index = 0


def get_next_key_set():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(KEY_SETS)
    return KEY_SETS[current_key_index]


def remove_u301_sequences(text):
    text = text.encode('unicode-escape').decode('utf-8')
    pattern = r'\\u3010.*?\\u3011'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

# Function to get top URLs based on the query
def get_organic_results(query, decrypted_serp_api_key, num_results=3):
    params = {
        "q": query,
        "engine": "google",
        "hl": "en",
        "num": str(num_results),
        "api_key": decrypted_serp_api_key
    }

    results = serpapi.search(params)

    # Check if 'organic_results' key is present in the results
    if 'organic_results' in results:
        organic_results = results['organic_results']
        urls = [result['link'] for result in organic_results[:num_results]]  # Extract the top 3 URLs
        return urls
    else:
        return []


def get_google_organic_results(query, decrypted_inputDeveloperKey, inputCSEId, num_results=3, try_count=0):
    global current_key_index
    print("insde Google: ", decrypted_inputDeveloperKey)
    try:
        # Initialize the Google API client
        service = googleapiclient.discovery.build("customsearch", "v1", developerKey=decrypted_inputDeveloperKey)

        # Make the search request
        res = service.cse().list(q=query, cx=inputCSEId, num=num_results).execute()

        # Extract the search results
        organic_results = res.get('items', [])
        urls = [result['link'] for result in organic_results]

        return urls
    except googleapiclient.errors.HttpError as e:
        print(f"An error occurred: {e}")
        if try_count < 2:  # allows for one retry
            next_key_set = get_next_key_set()
            print(next_key_set)
            return get_google_organic_results(query, next_key_set['api_key'], next_key_set['cse_id'], num_results, try_count + 1)
        else:
            return []


#Define the function to scrape data from a URL and return the URL 
def scrape_website(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, features="lxml")
        formatted_data = ' '.join(soup.text.split())
        return formatted_data
    except Exception as e:
        print(f"Error fetching URL {url}: {str(e)}")
        return "Failed to retrieve the webpage"
    

def combined_scrape_function(query, api_key, decrypted_inputDeveloperKey, num_results=3):
    client = OpenAI(api_key=api_key)
    # Get URLs from the search query
    urls = get_google_organic_results(query, decrypted_inputDeveloperKey, INPUT_CSE_ID, num_results=3, try_count=0)
    
    # Define max token limit
    max_tokens = 8000

    # Scrape and combine content from each URL
    combined_content = ''
    for url in urls:
        scraped_data = scrape_website(url)
        combined_content += scraped_data + '\n\n'  # Separate content from different URLs

    grounding_context = f"Context: {combined_content}\nUser Query: {query}"
    encoding = tiktoken.get_encoding('cl100k_base')
    grounding_context_tokens = len(encoding.encode(grounding_context))
    print("Intial grounding_context_tokens", grounding_context_tokens)

    # Truncate the grounding_context from the end if it exceeds max_tokens
    while grounding_context_tokens > max_tokens:
        # Calculate new length to keep 70% of the current content
        new_length = int(len(combined_content) * 0.8)
        combined_content = combined_content[:new_length]
        grounding_context = f"Context: {combined_content}\nUser Query: {query}"
        grounding_context_tokens = len(encoding.encode(grounding_context))
        print("Revised grounding_context_tokens", grounding_context_tokens)

    print("Final grounding_context_tokens", grounding_context_tokens)
    # Make completion request only if grounding_context is within token limit
    completion = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant, always return only the essential parts that answers the USER original USER query, but add 4 bullet points to backup your reasoning for the answer."},
            {"role": "user", "content": grounding_context}
        ]
    )

    response = completion.choices[0].message.content if completion.choices[0].message else ""
    return response, urls


def saveFileOpenAI(location, api_key):
    try:
        client = OpenAI(api_key=api_key)
        print("location: ", location)
        with open(location, "rb") as file:
            uploaded_file = client.files.create(file=file, purpose='assistants')
        return uploaded_file.id
    except FileNotFoundError:
        # Handle file not found error
        print("The file specified does not exist.")
    except Exception as e:
        # Handle any other exceptions
        print(f"An unexpected error occurred: {e}")
        return None


def startBotCreation(file_id_list, api_key, title, prompt, retrieval = False, web_browsing = False, code_interpreter = False):
    try:
        client = OpenAI(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v1"})
        name = title
        model = "gpt-4-vision-preview"

        tools = []
        if retrieval:
            tools.append({"type": "retrieval"})
        if code_interpreter:
            tools.append({"type": "code_interpreter"})
        if web_browsing:
            tools.append({"type": "function", "function": GET_ORGANIC_RESULTS_JSON})

        instructions = prompt + (GOOGLE_INSTRUCTIONS if web_browsing else "")

        print("tools:", tools)
        print("instructions:", instructions)

        assistant = client.beta.assistants.create(
            instructions=instructions,
            name=name,
            model=model,
            tools=tools,
            file_ids=file_id_list
        )
        print("assistant:", assistant)
        return assistant.id
    except Exception as e:
        # Handle specific exceptions if needed and log error details
        print(f"An error occurred during bot creation: {e}")
        return None


def delete_assistant(assistant_id, api_key):
    client = OpenAI(api_key=api_key)

    try:
        response = client.beta.assistants.delete(assistant_id)
        print(response)

        # Check if the deletion was successful
        if response.deleted:
            return "Assistant deleted successfully."
        else:
            return "Failed to delete assistant."

    except Exception as e:
        # Handle any exceptions that occur
        print("An error occurred:", e)
        return f"Error: {e}"


def delete_assistant_and_file(assistant_id, file_id, api_key):
    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=api_key)

        # Delete the file associated with the assistant
        deleted_assistant_file = client.beta.assistants.files.delete(
            assistant_id=assistant_id,
            file_id=file_id
        )
        print("Deleted assistant file:", deleted_assistant_file)

        # Delete the assistant
        response = client.beta.assistants.delete(assistant_id)
        print("Deleted assistant:", response)

        return True
    except Exception as e:
        # Log any exceptions and return False to indicate failure
        print(f"An error occurred: {e}")
        return False


def startThreadCreation(conversation, api_key):
    #client = OpenAI(api_key=api_key)
    print("1. hellooooooooooooooooooooooooooooooooooooooooooooooooooo")
    client = OpenAI(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})
    
    try:
        adjusted_conversation = [{"role": "user", "content": msg["content"]} for msg in conversation]
        response = client.beta.threads.create(messages=adjusted_conversation)
        print("startThreadCreation response:",response)
        # Check if the response has 'id' and 'object' attributes correctly
        if hasattr(response, 'id') and hasattr(response, 'object') and response.object == 'thread':
            print("startThreadCreation response.id:",response.id)
            return response.id
        else:
            return "Unexpected response format", 500

    except Exception as e:
        # Handle any exceptions that occur
        print("An error occurred:", e)
        return f"\nError: {e}", 500


def runAssistant(thread_id, assistant_id, api_key, decrypted_serp_api_key):
    print("2. hellooooooooooooooooooooooooooooooooooooooooooooooooooo")
    client = OpenAI(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})
    try:
        run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
        print("runAssistant thread_id:",thread_id)
        print("runAssistant assistant_id:",assistant_id)
        # Initialize a counter for the sleep duration
        sleep_duration = 0

        # Continuously check the status of the run
        while True:
            try:
                # Retrieve the run status
                run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                print("runAssistant run_status:", run_status)
                if run_status.status == 'completed':
                    # Retrieve messages from the thread
                    thread_messages_response = client.beta.threads.messages.list(thread_id=thread_id)
                    thread_messages = thread_messages_response.data
                    print("runAssistant run_status.status: completed")
                    # Find the latest assistant message
                    assistant_message = next((msg for msg in thread_messages if msg.role == 'assistant' and msg.content), None)

                    if assistant_message:
                        message_text = assistant_message.content[0].text.value
                        print("runAssistant message_text:",message_text)
                        # Check if there are annotations for a file citation
                        try:
                            if assistant_message.content[0].text.annotations:
                            #if assistant_message.content[0].text.annotations[0].file_citation.file_id:
                                #reference = assistant_message.content[0].text.annotations[0].file_citation.file_id

                                #latest
                                message_content = assistant_message.content[0].text
                                annotations = assistant_message.content[0].text.annotations
                                citations = []
                                #print(message_content, annotations, citations)
                                # Iterate over the annotations and add footnotes
                                for index, annotation in enumerate(annotations):
                                    # Replace the text with a footnote
                                    message_content.value = message_content.value.replace(annotation.text, f' [{index}]')

                                    # Gather citations based on annotation attributes
                                    if (file_citation := getattr(annotation, 'file_citation', None)):
                                        cited_file = client.files.retrieve(file_citation.file_id)
                                        citations.append(f'{file_citation.quote} from {cited_file.filename}')
                                    elif (file_path := getattr(annotation, 'file_path', None)):
                                        cited_file = client.files.retrieve(file_path.file_id)
                                        citations.append(f'Click <here> to download {cited_file.filename}')

                                #print("citations =", citations)
                                message_text = re.sub(r'【.*?】', '', message_text)
                                if citations[0]:
                                    message_text += "\n\n**Citations:**\n"
                                    message_text += '\n' + '\n'.join(citations)

                                reference = ""
                            else:
                                reference = ""
                        except:
                            reference = "" 

                        return message_text, reference
                    else:
                        return "No assistant messages found in the thread", None

                elif run_status.status == 'requires_action':
                    print("runAssistant run_status.status: requires_action")
                    tools_to_call = run_status.required_action.submit_tool_outputs.tool_calls
                    print(len(tools_to_call))
                    print(tools_to_call)

                    tool_output_array = []

                    for each_tool in tools_to_call:
                        try:
                            tool_call_id = each_tool.id
                            function_name = each_tool.function.name
                            function_arg = each_tool.function.arguments

                            print("Tool ID: ", tool_call_id)
                            print("Function to call: ", function_name)
                            print("Parameters to use: ", function_arg)

                            # Convert function_arg from JSON string to dictionary
                            function_arg_dict = json.loads(function_arg)

                            output = None  # Initialize output to None for safety
                            if function_name == 'get_organic_results':
                                # Access the 'query' key from the dictionary
                                print(function_arg_dict["query"])
                                web_data, urls = combined_scrape_function(function_arg_dict["query"], api_key, decrypted_serp_api_key)
                                output = web_data
                                print(output, urls)

                            tool_output_array.append({"tool_call_id": tool_call_id, "output": output})
                            print(tool_output_array)

                        except json.JSONDecodeError as e:
                            print(f"JSON parsing error: {e}")
                        except Exception as e:
                            print(f"Error processing tool: {e}")

                    # Assuming client is defined and authenticated
                    run = client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id, run_id=run.id, tool_outputs=tool_output_array)

                    while run.status not in ["completed", "failed"]:
                        print(run.status)
                        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

                    print("Exit Status:" , run.status)
                    messages = client.beta.threads.messages.list(thread_id=thread_id)

                    # Error handling for accessing message content
                    if messages.data:
                        message_content = messages.data[0].content  # Access the content of the first ThreadMessage
                        if message_content:
                            text_to_print = message_content[0].text.value  # Extract the text value
                            print(urls)
                            return text_to_print, urls
                    return None, "No messages found or message format not recognized"

                # Sleep for a short duration before next status check
                time.sleep(2)
                sleep_duration += 2

                # Check if the sleep duration has exceeded 10 seconds
                if sleep_duration > 300:
                    return f"Run status: Wait time exceeded ({sleep_duration} seconds)", None

            except Exception as e:
                return f"Error during run status check: {e}", None

    except Exception as e:
        return f"Error starting assistant run: {e}", None


def extract_text_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, features="lxml")
        #print(' '.join(soup.text.split()))
        return ' '.join(soup.text.split())
    except Exception as e:
        print(f"Error fetching URL {url}: {str(e)}")
        return ''


def get_youtube_video_id(url):
    """
    Given a YouTube video URL, returns the video ID.
    """
    if "youtube.com/watch?v=" in url:
        return url.split("youtube.com/watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube video URL")


def check_transcript_availability(video_id):
    """
    Check if an English transcript is available for the given YouTube video ID.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript_list.find_transcript(['en'])
        return True
    except Exception:
        return False


def get_transcript_content(video_id):
    """
    Fetch and return the English transcript of the given YouTube video ID as a single paragraph.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        full_text = " ".join([text['text'] for text in transcript])
        return full_text
    except Exception as e:
        raise ValueError(f"Error fetching transcript: {e}")
    

def process_url(url):
    try:
        # Check if the URL is a YouTube link
        if "youtube.com/watch?v=" in url or "youtu.be/" in url:
            video_id = get_youtube_video_id(url)
            
            # Check if a transcript is available
            if check_transcript_availability(video_id):
                return True, get_transcript_content(video_id)
            else:
                return False, "No transcript available for this YouTube video."
        else:
            # Extract text from a non-YouTube URL
            return True, extract_text_from_url(url)
    except Exception as e:
        return False, f"Error processing URL {url}: {str(e)}"
    
    
def sanitize_filename(filename):
    # Remove or replace special characters
    filename = re.sub('[\\\\/:*?"<>|@]', '_', filename)  # Replace with underscore
    # Optionally, trim the filename if it's too long
    # filename = filename[:255] if len(filename) > 255 else filename
    return filename
    

def compress_audio(file_path, user_folder, target_size_mb=24, initial_bitrate="64k"):
    # Function to convert bitrate string to integer kbps
    def bitrate_to_kbps(bitrate_str):
        return int(bitrate_str.replace("k", ""))

    # Calculate target size in bytes
    target_size = target_size_mb * 1024 * 1024

    # Check the size of the original file
    try:
        original_size = os.path.getsize(file_path)
    except FileNotFoundError:
        print("Error: File not found.")
        return None

    if original_size <= target_size:
        print("File is already under the target size.")
        return file_path, original_size

    # Load the audio file
    try:
        audio = AudioSegment.from_file(file_path)
    except Exception as e:
        print(f"Error loading audio file: {e}")
        return None

    # Extract file name without path and extension
    file_name = os.path.basename(file_path)
    file_name, file_extension = os.path.splitext(file_name)
    bitrate = initial_bitrate

    while True:
        compressed_file_name = f"{file_name}_compressed_{bitrate}{file_extension}"
        compressed_file_path = os.path.join(user_folder, compressed_file_name)
        
        # Export the file with the new bitrate
        try:
            audio.export(compressed_file_path, format=file_extension[1:], bitrate=bitrate)
        except Exception as e:
            print(f"Error exporting audio file: {e}")
            return None

        # Check the size of the compressed file
        compressed_size = os.path.getsize(compressed_file_path)

        if compressed_size <= target_size:
            break

        # Reduce bitrate for further compression
        current_bitrate_kbps = bitrate_to_kbps(bitrate)
        if current_bitrate_kbps <= 32:  # Avoid going too low in bitrate
            print("Warning: Unable to compress to target size with acceptable quality.")
            break
        bitrate = f"{current_bitrate_kbps // 2}k"

    return compressed_file_path, compressed_size


def compressed_audio_to_text_file(compressed_file_path, user_folder, api_key):
    try:
        with open(compressed_file_path, "rb") as audio_file:
            client = openai.OpenAI(api_key=api_key)
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="text"
            )

        # Create a text file in the user_folder to save the transcript
        file_name, _ = os.path.splitext(os.path.basename(compressed_file_path))
        transcript_file_path = os.path.join(user_folder, f"{file_name}_transcript.txt")

        with open(transcript_file_path, "w") as text_file:
            text_file.write(transcript_response)

        return transcript_file_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
