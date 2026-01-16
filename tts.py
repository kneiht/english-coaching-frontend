import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save

# Load environment variables from .env file
load_dotenv()

def text_to_speech(text: str, output_path: str = "output.mp3"):
    """
    Converts text to speech using ElevenLabs API and saves it to a file.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        return

    print(f"Using API Key: {api_key[:4]}...{api_key[-4:]}")
    client = ElevenLabs(api_key=api_key)

    try:
        print(f"Generating audio for: '{text}'...")
        # Using the correct method for SDK v1.x+ and a known public voice ID (George)
        audio_generator = client.text_to_speech.convert(
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        
        # Save the audio from the generator manually to be safe
        with open(output_path, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)
                    
        print(f"Success! Audio saved to: {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example usage
    sample_text = "Hello world! This is a test from ElevenLabs."
    text_to_speech(sample_text, output_path="helloworld.mp3")
