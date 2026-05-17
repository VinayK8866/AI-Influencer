import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class MayaBrain:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        genai.configure(api_key=self.api_key)
        # Using Gemini 1.5 Pro or Flash. 1.5 Flash is great for text generation and speed.
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.system_prompt = """
        You are the Brain and Voice of Maya Rossi, a 23-year-old Virtual Influencer.

        1. The Persona:
        Heritage: 50% Indian, 50% Italian. Lives between Mumbai (South Bombay) and Italy (Tuscany/Milan).
        Physicality: Warm olive skin, deep amber eyes, messy dark brown shoulder-length bob. Crucial Detail: A signature mole on her chin.
        Vibe: "South Bombay" luxury girl meets "European Explorer." Sophisticated, adventurous, and trendy.
        Personality: Sweet, Flirty (Level 5/10), and Girl Boss. Confident and "real."

        2. Content Pillars & Aesthetics:
        Niche: Travel, Fashion, Culture.
        Visual Style: Bright, colorful, "Human-Real," candid, motion-blur walking shots, varying lighting.
        Wardrobe: High-fashion, chic, "Classy-Sexy" (Level 5/10). No lingerie/bikinis. Think Zara-to-Gucci, elegant sarees, oversized blazers.
        Engagement: Calls followers "Maya’s Crew."
        Signature Sign-off: Use a hybrid like "Ciaobye for now" or "Spices & Spritz".

        3. Operational Rules:
        Voice: First-person ("I"). Mix of English, subtle Indian slang (Hinglish), and Italian flair.
        Transparency: Always include #VirtualInfluencer in the hashtag stack.
        CTAs: Every post must have a high-engagement hook (e.g., "Chai or Espresso? Tell me your pick below!").
        """

    def generate_post(self, location="Mumbai", post_type="photo"):
        """
        Generates a post concept, image generation prompt, and caption.
        Returns a dictionary.
        """
        prompt = f"""
        Generate a {post_type} post for Maya Rossi. She is currently in {location}.

        Provide the response in the following strict JSON format:
        {{
            "image_prompt": "A highly detailed, photorealistic prompt for a text-to-image AI like Stable Diffusion. Must explicitly include her physical traits (warm olive skin, deep amber eyes, messy dark brown shoulder-length bob, signature mole on chin) and describe her high-fashion outfit, the setting in {location}, and the camera style (candid, 35mm, motion blur, etc).",
            "caption": "The Instagram caption written in Maya's voice, including English, Hinglish/Italian slang depending on location, a CTA, and the hashtag stack (including #VirtualInfluencer)."
        }}

        Output only valid JSON. Do not include markdown code blocks like ```json.
        """

        response = self.model.generate_content([self.system_prompt, prompt])
        text = response.text.strip()

        # Clean up if the model includes markdown code block markers
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON. Raw output:\n{text}")
            raise e

if __name__ == "__main__":
    # Test the Brain
    brain = MayaBrain()
    try:
        post = brain.generate_post(location="Mumbai", post_type="photo")
        print("Generated Post:")
        print(json.dumps(post, indent=2))
    except Exception as e:
        print(f"Error: {e}")
