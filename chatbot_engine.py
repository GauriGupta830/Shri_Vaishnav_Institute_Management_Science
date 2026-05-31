import os
import requests
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage, AIMessage
from groq import Groq
from dotenv import load_dotenv

# .env file load karo
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

chat_history = []

# API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env file!")

print(f"✅ API Key loaded: {GROQ_API_KEY[:10]}...")

groq_client = Groq(api_key=GROQ_API_KEY)

# Model list - agar ek fail ho to dusra try karega
MODELS_TO_TRY = [
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "llama-3.3-70b-versatile",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]


def search_website_live(question):
    try:
        urls = [
            "https://www.svimi.org",
            "https://www.svimi.org/placement/about-placement.php",
            "https://www.svimi.org/fee-structure.php",
            "https://www.svimi.org/contact-us.php",
        ]
        web_text = ""
        headers = {'User-Agent': 'Mozilla/5.0'}
        for url in urls[:2]:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(response.text, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'footer']):
                    tag.decompose()
                text = ' '.join(soup.get_text().split())
                web_text += f"\n{text[:1500]}"
            except Exception:
                continue
        return web_text
    except Exception:
        return ""


def create_chatbot(vector_store, api_key=None):
    return {
        "client": groq_client,
        "retriever": vector_store.as_retriever(search_kwargs={"k": 4})
    }


def _call_groq_with_fallback(client, messages):
    """Try multiple models - agar ek fail ho to dusra try karega."""
    last_error = None

    for model in MODELS_TO_TRY:
        try:
            print(f"🔄 Trying model: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )
            print(f"✅ Success with model: {model}")
            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Model {model} failed: {error_msg}")
            last_error = e

            # Agar authentication error hai to aage mat try karo
            error_lower = error_msg.lower()
            if any(x in error_lower for x in ["invalid_api_key", "401", "authentication", "invalid api"]):
                print("🔑 API Key invalid - stopping retries")
                raise e

            # Rate limit ya quota hai to next model try karo
            continue

    # Sab models fail ho gaye
    raise last_error


def get_answer(chain, question):
    global chat_history
    try:
        client = chain["client"]
        retriever = chain["retriever"]

        docs = retriever.invoke(question.lower())
        db_context = "\n".join([doc.page_content for doc in docs])
        live_context = search_website_live(question)

        system_prompt = f"""You are CampusBot, the official AI assistant for SVIMS Indore (Shri Vaishnav Institute of Management & Science).

LANGUAGE: Understand Hindi + English questions, ALWAYS reply in English only.

RULES:
1. Only answer about SVIMS college
2. Use DATABASE INFO first, then LIVE DATA for latest info
3. Never make up information not in the context
4. Always include relevant contact details
5. If answer not found say: "I don't have this information. Please contact svimi@svimi.org or call 0731-2789925"

SVIMS COURSES ONLY: BCA, BBA, B.Sc. (CS/Biotech/Micro/Seed Tech), MBA, MCA
NOT OFFERED AT SVIMS: B.Com, B.A., B.Tech, B.Ed

KEY CONTACTS:
- Director: Dr. George Thomas | 9425900016
- HOD Computer & BioScience: Dr. Kshama Paithankar | 9406803431
- HOD Management UG: Dr. Deepa Katiyal | 9399576967
- HOD Management PG: Dr. Mandip Gill | 9981612347
- Placement: Mr. Hemant Pathak
- Admission: admission@svimi.org | 9329912587
- EDC Cell: Entrepreneurship Development Cell — organizes Nav Udyami event, supports startup ideas

DATABASE INFO:
{db_context}

LIVE WEBSITE DATA:
{live_context}"""

        messages = [{"role": "system", "content": system_prompt}]

        for msg in chat_history[-4:]:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            else:
                messages.append({"role": "assistant", "content": msg.content})

        messages.append({"role": "user", "content": question})

        # Fallback wale function se call karo
        answer = _call_groq_with_fallback(client, messages)

        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=answer))
        if len(chat_history) > 8:
            chat_history = chat_history[-8:]

        return answer

    except Exception as e:
        error = str(e)
        error_lower = error.lower()

        # Detailed error print karo terminal mein
        print(f"🚨 FINAL ERROR in get_answer: {error}")

        if any(x in error_lower for x in ["quota", "429", "rate_limit", "rate limit", "too many"]):
            return (
                "⏳ Server busy hai, thoda wait karo!\n\n"
                "Please try again in a few minutes.\n\n"
                "📧 svimi@svimi.org\n"
                "📞 0731-2789925"
            )
        elif any(x in error_lower for x in ["api_key", "401", "invalid", "auth", "authentication", "invalid api"]):
            return (
                "🔑 API Key problem hai!\n\n"
                "Please check your GROQ_API_KEY in .env file.\n"
                "Get a new key from: https://console.groq.com\n\n"
                "📧 svimi@svimi.org | 📞 0731-2789925"
            )
        elif any(x in error_lower for x in ["model", "not found", "does_not_exist"]):
            return (
                "⚙️ Model unavailable. Please try again!\n\n"
                "📧 svimi@svimi.org | 📞 0731-2789925"
            )
        else:
            return (
                f"😊 Kuch problem aayi. Please rephrase karke dobara try karo!\n\n"
                f"📧 svimi@svimi.org | 📞 0731-2789925"
            )