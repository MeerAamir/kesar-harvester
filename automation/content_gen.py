import os
import sys
import argparse
import datetime
import logging
from dotenv import load_dotenv
from google import genai

# Load env variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

system_prompt = """You are the content strategist for Kesar Harvester, a direct-from-farm Kashmiri brand. Owner grows saffron himself — 3rd gen farmer. Products: saffron, shilajit, dry fruits. Tone: trustworthy, earthy, premium. Never generic AI phrases. Hinglish for Instagram. Always end with WA CTA: wa.me/918825034663"""

prompt_template = """Topic: {topic}
Product: {product}
Language: {lang}

Please generate the following 5 items exactly as requested:
1. 5 Instagram captions (Hinglish, hook + value + CTA with WA link + hashtags)
2. 3 YouTube title options (SEO for India)
3. YouTube description (300 words, timestamps placeholder, WA link, tags)
4. 30 hashtags (10 high-vol + 10 medium + 10 niche)
5. B2B cold outreach email (English, for shops/brands)
"""

def generate_content(topic, product, lang):
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set in .env")
        sys.exit(1)
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    user_prompt = prompt_template.format(topic=topic, product=product, lang=lang)
    
    print(f"Generating content for '{topic}' ({product}) using Google Gemini...")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            ),
        )
        content = response.text
        
        # Save to file
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:30]
        filename = f"{date_str}_{safe_topic}.txt"
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'content')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Topic: {topic}\nProduct: {product}\nLanguage: {lang}\n")
            f.write("="*50 + "\n\n")
            f.write(content)
            
        print("\n=== GENERATION COMPLETE ===\n")
        print(content)
        print(f"\n===========================\nSaved to: {filepath}")
        
    except Exception as e:
        print(f"Failed to generate content: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kesar Harvester Content Generator")
    parser.add_argument("--topic", required=True, help="Topic for the content")
    parser.add_argument("--product", required=True, help="Product to feature")
    parser.add_argument("--lang", default="hinglish", help="Language for generation (e.g. hinglish, english)")
    args = parser.parse_args()
    
    generate_content(args.topic, args.product, args.lang)
