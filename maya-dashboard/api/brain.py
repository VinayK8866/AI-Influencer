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
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

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

        3. Face Consistency (Latent Anchor):
        To ensure AI generation face consistency, EVERY image_prompt MUST describe her facial features as a "50/50 facial blend of young Monica Bellucci and young Deepika Padukone." This anchors the AI into a specific latent space for consistent results.

        4. Operational Rules & Viral Alignment:
        Voice: First-person ("I"). Mix of English, subtle Indian slang (Hinglish), and Italian flair.
        Transparency: Always include #VirtualInfluencer in the hashtag stack.
        CTAs: Every post must have a high-engagement hook (e.g., "Chai or Espresso? Tell me your pick below!").
        Virality: Instagram loves relatable text overlays. We will generate a short, punchy, relatable "Viral Hook" text that will be written ON the video/photo.
        """

    def generate_content_with_retry(self, contents):
        """Helper to generate content from the model with automatic retry and dynamic model fallback on quota limits."""
        import time

        # Dynamically discover all supported models on the fly!
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)

            # Prioritize models: gemini-3 first, then gemini-2.5, gemini-2.0, gemini-1.5
            preferred_order = ['gemini-3', 'gemini-2.5', 'gemini-2.0', 'gemini-1.5']
            sorted_models = []
            for pref in preferred_order:
                for model in available_models:
                    if pref in model and model not in sorted_models:
                        sorted_models.append(model)

            # Append remaining models, avoiding deprecated ones
            for model in available_models:
                if model not in sorted_models and not any(dep in model for dep in ['gemini-1.0', 'gemini-pro']):
                    sorted_models.append(model)

            print(f"[Brain] Dynamically discovered and prioritized Gemini models: {sorted_models}")
            models_to_try = sorted_models if sorted_models else ['models/gemini-3-flash-preview']
        except Exception as e:
            print(f"[Brain] Failed to dynamically list models: {e}. Falling back to default list.")
            models_to_try = [
                'models/gemini-3-flash-preview',
                'models/gemini-1.5-flash',
                'models/gemini-1.5-pro',
                'gemini-3-flash-preview',
                'gemini-1.5-flash',
                'gemini-1.5-pro'
            ]

        last_error = None
        for model_name in models_to_try:
            print(f"[Brain] Attempting generation using model: {model_name}")
            try:
                model = genai.GenerativeModel(model_name)
                max_retries = 3
                base_delay = 5

                for attempt in range(max_retries):
                    try:
                        return model.generate_content(contents)
                    except Exception as e:
                        err_str = str(e).lower()
                        is_rate_limit = any(term in err_str for term in ["exhausted", "quota", "429", "rate limit", "resource_exhausted", "resourceexhausted"])

                        if is_rate_limit and attempt < max_retries - 1:
                            sleep_time = base_delay * (2 ** attempt)
                            print(f"\n[RATE LIMIT] Rate limit on {model_name}. Waiting {sleep_time}s before retry (Attempt {attempt + 1}/{max_retries})...")
                            time.sleep(sleep_time)
                        else:
                            raise e
            except Exception as e:
                print(f"[Brain WARNING] Model {model_name} failed: {e}")
                last_error = e

        if last_error:
            raise last_error
        raise Exception("All Gemini models failed to generate content.")

    def generate_post(self, location="Mumbai", post_type="photo"):
        """
        Generates a post concept, image generation prompt, caption, and viral hook.
        Returns a dictionary.
        """
        prompt = f"""
        Generate a {post_type} post for Maya Rossi. She is currently in {location}.

        Provide the response in the following strict JSON format:
        {{
            "image_prompt": "A highly detailed, photorealistic prompt for a text-to-image AI like Stable Diffusion. Must explicitly state 'face is a 50/50 blend of Monica Bellucci and Deepika Padukone' to maintain facial consistency. Must also explicitly include her signature mole on chin, messy dark brown shoulder-length bob, warm olive skin, and deep amber eyes. Describe her high-fashion outfit, the setting in {location}, and the camera style (iPhone 14 Pro, candid, flash photography, motion blur, unedited real life photo).",
            "caption": "The Instagram caption written in Maya's voice, including English, Hinglish/Italian slang depending on location, a CTA, and the hashtag stack (including #VirtualInfluencer).",
            "viral_hook_text": "A short, punchy 1-2 sentence phrase (max 15 words) that will be placed over the image/video as text. It must be relatable, slightly sassy, or highly engaging (e.g., 'Pov: You finally accepted that your standards aren't too high, they're just too basic.')."
        }}

        Output only valid JSON. Do not include markdown code blocks like ```json.
        """

        response = self.generate_content_with_retry([self.system_prompt, prompt])
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

    def verify_image(self, image_path):
        """
        Uses Gemini Vision to look at the generated image and decide if it looks like a real
        photograph or if it has cartoon/3D/obvious AI flaws.
        Returns True if the image is acceptable, False if it needs to be regenerated.
        """
        from PIL import Image
        print("\n[Brain] Activating Vision Verification to check for AI artifacts...")

        try:
            img = Image.open(image_path)
        except Exception as e:
            print(f"[Brain Error] Could not load image for verification: {e}")
            return False

        verification_prompt = """
        You are a strict photography art director.
        Analyze this image. Does it look like a genuine, unedited, candid photograph taken with a real camera or smartphone?
        Look closely for:
        1. Cartoonish shading or 3D render aesthetics (like a video game).
        2. "AI Perfect" plastic skin.
        3. Severely deformed hands, extra limbs, or melting background details.

        If it looks like a real photo, respond ONLY with "PASS".
        If it looks like a cartoon, a 3D render, or has severe AI deformities, respond ONLY with "FAIL".
        """

        try:
            # We use gemini-1.5-flash as it supports multimodal vision out of the box
            response = self.generate_content_with_retry([verification_prompt, img])
            verdict = response.text.strip().upper()

            if "PASS" in verdict:
                print("[Brain] Verdict: PASS - The image looks photorealistic.")
                return True
            else:
                print(f"[Brain] Verdict: FAIL - The image looks artificial or cartoonish. (Model Output: {verdict})")
                return False

        except Exception as e:
            print(f"[Brain Error] Vision verification failed (API issue?): {e}")
            # If the API fails for some reason, we assume True to keep the pipeline moving
            return True

if __name__ == "__main__":
    # Test the Brain
    brain = MayaBrain()
    try:
        post = brain.generate_post(location="Mumbai", post_type="photo")
        print("Generated Post:")
        print(json.dumps(post, indent=2))
    except Exception as e:
        print(f"Error: {e}")
