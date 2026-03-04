import os
import wave
import json
import argparse
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GeminiTTS:
    """
    GEMINI 2.5 PRO/FLASH TTS ADVANCED WRAPPER
    -----------------------------------------
    TÀI LIỆU HƯỚNG DẪN DÀNH CHO AI AGENT & DEVELOPER:

    1. THIẾT LẬP (SETUP):
       - Thư viện: pip install google-genai python-dotenv
       - API Key: Phải có GOOGLE_API_KEY trong file .env

    2. DANH SÁCH 30 GIỌNG NÓI KHẢ DỤNG (voice_name):
       [Name] - [Style]
       ----------------
       Zephyr - Bright          Puck - Upbeat           Charon - Informative
       Kore - Firm              Fenrir - Excitable      Leda - Youthful
       Orus - Firm              Aoede - Breezy          Callirrhoe - Easy-going
       Autonoe - Bright         Enceladus - Breathy     Iapetus - Clear
       Umbriel - Easy-going     Algieba - Smooth        Despina - Smooth
       Erinome - Clear          Algenib - Gravelly      Rasalgethi - Informative
       Laomedeia - Upbeat       Achernar - Soft         Alnilam - Firm
       Schedar - Even           Gacrux - Mature         Pulcherrima - Forward
       Achird - Friendly        Zubenelgenubi - Casual  Vindemiatrix - Gentle
       Sadachbia - Lively       Sadaltager - Knowledgeable Sulafat - Warm

    3. CHIẾN LƯỢC PROMPT (DIRECTOR'S NOTES):
       Gemini TTS không chỉ là text-to-speech, nó là LLM có khả năng diễn xuất.
       Để điều chỉnh giọng đọc, hãy sử dụng 'director_notes' với các thành phần:
       - Audio Profile: Xác định nhân vật (Age, Gender, Trait).
       - Scene: Mô tả môi trường (Studio, Outdoor, Large hall).
       - Director's Notes: Gaya, Accent (US, UK, Australian, Vietnamese...), Emotion, Speed, Breathing.
       Ví dụ: "Director's Notes: Accent: British, Tone: Excited, Speed: Fast, Style: Radio DJ"

    4. ĐỊNH DẠNG JSON ĐẦU VÀO:
       - Single Speaker:
         { "type": "single", "text": "...", "voice_name": "Kore", "director_notes": "..." }
       - Multi-Speaker (Maks 2 người nói):
         { 
           "type": "multi", 
           "conversation": ["Name1: Hello", "Name2: Hi there"],
           "speakers": {"Name1": "Kore", "Name2": "Puck"}
         }

    5. CÁCH CHẠY DÒNG LỆNH:
       python tts_gemini_advanced.py -j input.json -o output.wav
    """

    def __init__(self, api_key=None, model_id="gemini-2.5-flash-preview-tts"):
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY không được tìm thấy.")
        self.client = genai.Client(api_key=key)
        self.model_id = model_id 

    def save_wave_file(self, filename, pcm_data, channels=1, rate=24000, sample_width=2):
        """Lưu dữ liệu PCM thô vào định dạng .wav chuyên dụng cho Gemini TTS output (24kHz)"""
        try:
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(pcm_data)
            print(f"✅ Created: {filename}")
        except Exception as e:
            print(f"❌ Error saving wave: {e}")

    def generate_single_speaker(self, text, voice_name="Kore", output_file="output.wav", director_notes=""):
        """Tạo audio đơn người nói với khả năng tùy chỉnh Accent/Emotion qua Director's Notes"""
        prompt = f"{director_notes}\n\nTranscript: {text}" if director_notes else text
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                        )
                    ),
                )
            )
            audio_data = self._extract_audio(response)
            if audio_data:
                self.save_wave_file(output_file, audio_data)
        except Exception as e:
            print(f"❌ API Error: {e}")

    def generate_multi_speaker(self, conversation_parts, speaker_configs, output_file="output.wav"):
        """Tạo audio hội thoại nhiều người nói"""
        prompt = "TTS the following conversation:\n" + "\n".join(conversation_parts)
        voice_configs = [
            types.SpeakerVoiceConfig(
                speaker=name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=vname)
                )
            ) for name, vname in speaker_configs.items()
        ]

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=voice_configs
                        )
                    ),
                )
            )
            audio_data = self._extract_audio(response)
            if audio_data:
                self.save_wave_file(output_file, audio_data)
        except Exception as e:
            print(f"❌ API Error: {e}")

    def generate_from_json(self, json_input, output_file="output.wav"):
        """
        Tạo audio từ dữ liệu JSON (chuỗi hoặc đường dẫn file).
        """
        if os.path.isfile(json_input):
            with open(json_input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = json.loads(json_input)

        if "vocab" in data:
            self.process_vocab_json(data)
            return

        mode = data.get("type", "single")
        
        if mode == "single":
            self.generate_single_speaker(
                text=data.get("text", ""),
                voice_name=data.get("voice_name", "Kore"),
                output_file=output_file,
                director_notes=data.get("director_notes", "")
            )
        elif mode == "multi":
            self.generate_multi_speaker(
                conversation_parts=data.get("conversation", []),
                speaker_configs=data.get("speakers", {}),
                output_file=output_file
            )
        else:
            print(f"❌ JSON Type không hợp lệ: {mode}")

    def process_vocab_json(self, data, words_dir="wait-upload/audio-words", sentences_dir="wait-upload/audio-sentences", voice_name="Kore"):
        """
        Xử lý file vocab.txt để tạo audio cho từ và câu.
        """
        # Đảm bảo thư mục tồn tại
        os.makedirs(words_dir, exist_ok=True)
        os.makedirs(sentences_dir, exist_ok=True)

        vocab_list = data.get("vocab", [])
        print(f"📦 Processing {len(vocab_list)} vocab entries...")

        # Director notes cho giọng đọc mang tính giáo dục
        word_notes = "Director's Notes: Accent: US, Style: Educational, Tone: Clear, Speed: Normal"
        sentence_notes = "Director's Notes: Accent: US, Style: Educational, Tone: Clear, Speed: Normal"

        for entry in vocab_list:
            word = entry.get("word")
            sentence = entry.get("sampleSentence")
            word_file = entry.get("wordPronunciation")
            sentence_file = entry.get("sentencePronunciation")

            if word and word_file:
                output_path = os.path.join(words_dir, word_file)
                if os.path.exists(output_path):
                    print(f"⏩ Skipping existing word: {word}")
                else:
                    print(f"🎤 Generating word: {word}")
                    self.generate_single_speaker(text=word, voice_name=voice_name, output_file=output_path, director_notes=word_notes)
                    time.sleep(6) # Respect rate limit: 10 requests per minute

            if sentence and sentence_file:
                output_path = os.path.join(sentences_dir, sentence_file)
                if os.path.exists(output_path):
                    print(f"⏩ Skipping existing sentence: {sentence}")
                else:
                    print(f"🎤 Generating sentence: {sentence}")
                    self.generate_single_speaker(text=sentence, voice_name=voice_name, output_file=output_path, director_notes=sentence_notes)
                    time.sleep(7) # Respect rate limit: 10 requests per minute

        print("✅ Finished processing vocab audio.")

    def _extract_audio(self, response):
        """Trích xuất dữ liệu binary từ response parts"""
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini 2.5 Pro/Flash TTS Script")
    parser.add_argument("-j", "--json", help="Đường dẫn tới file JSON chứa nội dung TTS")
    parser.add_argument("-v", "--vocab", help="Đường dẫn tới file vocab.txt để gộp tạo audio")
    parser.add_argument("-o", "--output", help="Tên file audio đầu ra (mặc định: output.wav)", default="output.wav")
    parser.add_argument("--words-dir", help="Thư mục lưu audio từ vựng", default="wait-upload/audio-words")
    parser.add_argument("--sentences-dir", help="Thư mục lưu audio câu mẫu", default="wait-upload/audio-sentences")
    
    args = parser.parse_args()

    try:
        tts = GeminiTTS()
        if args.vocab:
            with open(args.vocab, 'r', encoding='utf-8') as f:
                data = json.load(f)
            tts.process_vocab_json(
                data, 
                words_dir=args.words_dir, 
                sentences_dir=args.sentences_dir
            )
        elif args.json:
            tts.generate_from_json(args.json, output_file=args.output)
        else:
            parser.print_help()
    except Exception as e:
        print(f"❌ Lỗi: {e}")
