import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "openai/gpt-oss-120b"


def translate_to_english(text: str) -> dict:

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are a language detection and translation component
for a weather application.

Detect the language of the user's question and translate
the question into English.

Preserve:
- city names
- locations
- dates
- numbers
- weather-related meaning

Return ONLY in this exact format:

LANGUAGE: <language>
ENGLISH: <translated question>
"""
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content.strip()

    language = "English"
    english_text = text

    for line in result.splitlines():

        if line.startswith("LANGUAGE:"):
            language = line.replace(
                "LANGUAGE:", ""
            ).strip()

        elif line.startswith("ENGLISH:"):
            english_text = line.replace(
                "ENGLISH:", ""
            ).strip()

    return {
        "language": language,
        "english": english_text
    }


def translate_from_english(
    text: str,
    target_language: str
) -> str:

    if target_language.lower() == "english":
        return text

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""
Translate the following weather response into
{target_language}.

Preserve:
- temperatures
- percentages
- dates
- city names
- weather information
- meaning

Do not add or remove information.

Return ONLY the translated response.
"""
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()