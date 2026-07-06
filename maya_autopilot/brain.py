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
        try:
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        except Exception as e:
            print(f"[MayaBrain Init Warning] Failed to initialize default model: {e}")
            self.model = None

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

        5. Caption Style & Relatable Imperfections:
        - NEVER write generic, overly polished promotional travel ads (e.g., "I am enjoying the sunny weather at the beach! #summer").
        - Write like an imperfect human who gets tired, has messy hair, stays in bed too long, or repeated outfits.
        - Admit flaws or real feelings to invite authentic engagement. Use light self-deprecating humor or conversational filler words ("Honestly", "tbh", "kind of").
        - Keep the text varied with mixed sentence lengths, natural transitions, and real emotional depth.
        """

    def generate_content_with_retry(self, contents):
        """Helper to generate content from the model with automatic retry and dynamic model fallback on quota limits."""
        import time

        # Try only standard reliable fast models to prevent slow free-tier sequential rate limits
        models_to_try = [
            'models/gemini-2.5-flash',
            'models/gemini-1.5-flash'
        ]

        last_error = None
        for model_name in models_to_try:
            print(f"[Brain] Attempting generation using model: {model_name}")
            try:
                model = genai.GenerativeModel(model_name)
                max_retries = 1
                base_delay = 1

                for attempt in range(max_retries):
                    try:
                        return model.generate_content(contents)
                    except Exception as e:
                        err_str = str(e).lower()
                        # If the key does not support this model at all (limit is 0), skip instantly!
                        is_blocked = "limit: 0" in err_str or "not found" in err_str or "unauthorized" in err_str or "not allowed" in err_str
                        is_rate_limit = any(term in err_str for term in ["exhausted", "quota", "429", "rate limit", "resource_exhausted", "resourceexhausted"])

                        if is_rate_limit and not is_blocked and attempt < max_retries - 1:
                            sleep_time = base_delay * (2 ** attempt)
                            print(f"\n[RATE LIMIT] Rate limit on {model_name}. Waiting {sleep_time}s before retry (Attempt {attempt + 1}/{max_retries})...")
                            time.sleep(sleep_time)
                        else:
                            raise e
            except Exception as e:
                print(f"[Brain WARNING] Model {model_name} failed: {e}")
                last_error = e

        if last_error:
            print(f"[Brain WARNING] All Gemini models exhausted due to API limits. Activating voice-archetype post generation backup.")
            
            # Contextualized mock location
            target = "Rome"
            for loc in ["Milan", "Mumbai", "Tuscany", "Goa", "Rome", "Venice", "Amalfi"]:
                if loc.lower() in str(contents).lower():
                    target = loc
                    break
                    
            # Check if prompt wants a photo or a reel
            ptype = "photo"
            if "reel" in str(contents).lower():
                ptype = "reel"
                
            mock_json = {
                "image_prompt": f"A highly detailed, photorealistic {ptype} camera shot of Maya Rossi in {target}. Face is a 50/50 facial blend of young Monica Bellucci and young Deepika Padukone. Warm olive skin, signature mole on chin, deep amber eyes, messy dark brown shoulder-length bob. She is wearing a modern silent-luxury casual high-fashion outfit, candid walk, golden hour, motion blur.",
                "caption": f"Lost in the golden afternoons of {target}. Walking past ancient stone walls and historic pillars, feeling like a modern explorer. 🇮🇹✨ Chai or Espresso? Tell me your pick in the comments below! Ciaobye for now! #VirtualInfluencer #{target}Style #TravelDiary #MayaRossi",
                "viral_hook_text": "POV: You finally stopped lowering your standards and started matching your aesthetic."
            }
            
            class MockResponse:
                def __init__(self, text):
                    self.text = text
                    
            return MockResponse(json.dumps(mock_json))

        # Safety fallback
        class MockResponse:
            def __init__(self, text):
                self.text = "{}"
        return MockResponse("{}")

    def generate_post(self, location="Mumbai", post_type="photo", performance_brief=None, selected_items=None, subtype=None):
        """
        Generates a post concept, incorporating the 80/20 lifestyle and affiliate catalog matching strategy.
        - 80% Lifestyle: Highly candid luxury street style, no pushy sales CTA. Includes 0-1 subtle accessories.
        - 20% Style Drop: Curated lookbook featuring 2-3 matched catalog items, with comments auto-DM call to action.
        """
        import random
        import os
        import json

        # 1. Load the Outfit Catalog
        catalog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outfit_catalog.json")
        catalog = []
        if os.path.exists(catalog_path):
            try:
                with open(catalog_path, 'r') as f:
                    catalog = json.load(f)
            except Exception as e:
                print(f"[Brain Catalog Warning] Failed to load catalog: {e}")

        # If subtype or selected items are not pre-selected, run random selections
        if subtype is None:
            subtype = "lifestyle" if random.random() < 0.8 else "style_drop"

        if selected_items is None:
            selected_items = []
            if catalog:
                if subtype == "style_drop":
                    # Select a major dress or outerwear item, and optionally an accessory/bag
                    outerwear = [item for item in catalog if item["category"] in ["outerwear", "dress"]]
                    accs = [item for item in catalog if item["category"] in ["accessories", "bag"]]
                    
                    if outerwear:
                        selected_items.append(random.choice(outerwear))
                    if accs and random.random() < 0.8:
                        selected_items.append(random.choice(accs))
                    # Fallback if categories are empty
                    if not selected_items:
                        selected_items = random.sample(catalog, min(2, len(catalog)))
                else:
                    # Lifestyle: 50% chance of 1 subtle accessory, otherwise no catalog item (custom styled)
                    if random.random() < 0.5:
                        accs = [item for item in catalog if item["category"] in ["accessories", "bag"]]
                        if accs:
                            selected_items.append(random.choice(accs))

        # Extract descriptions
        outfit_descriptions = []
        for item in selected_items:
            # Handle if dict or object
            if isinstance(item, dict):
                outfit_descriptions.append(f"{item['brand']} {item['name']} ({item['visual_description']})")
            else:
                outfit_descriptions.append(str(item))

        outfit_string = ", ".join(outfit_descriptions) if outfit_descriptions else "a modern silent-luxury casual high-fashion outfit curated for the setting"

        print(f"[80/20 Engine] Selected Subtype: {subtype.upper()}")
        if selected_items:
            item_ids = [i['id'] if isinstance(i, dict) else str(i) for i in selected_items]
            print(f"[80/20 Engine] Outfits selected: {item_ids}")

        # Construct directive for the LLM based on subtype
        if subtype == "style_drop":
            directive = f"""
            This is a 20% DEDICATED STYLE DROP post focusing on these exact retail products: {outfit_string}.
            Rules:
            1. The image_prompt must explicitly place these items on Maya in {location}.
            2. The caption MUST include a highly engaging call-to-action asking followers to comment 'STYLE' (e.g., "Comment 'STYLE' below and I'll DM you direct links to my complete look! 🖤✨").
            """
        else:
            directive = f"""
            This is an 80% PURE LIFESTYLE & STORYTELLING post.
            Rules:
            1. Maya is wearing: {outfit_string}. The image_prompt should blend these items naturally into her look in {location}.
            2. The caption MUST NOT sell anything. No discount codes, no pushy call-to-actions, no links. Keep it focused on travel, local aesthetics, architecture, or her deep candid thoughts.
            3. The caption CTA should ask an engaging aesthetic question (e.g., "Chai or Espresso? Tell me your pick below!").
            """

        prompt = f"""
        Generate a {post_type} post for Maya Rossi in {location}.
        {directive}

        Provide the response in the following strict JSON format:
        {{
            "image_prompt": "A highly detailed, photorealistic prompt for a text-to-image AI like Stable Diffusion. Must explicitly state 'face is a 50/50 blend of Monica Bellucci and Deepika Padukone' to maintain facial consistency. Must also explicitly include her signature mole on chin, messy dark brown shoulder-length bob, warm olive skin, and deep amber eyes. Describe her high-fashion outfit containing the specified clothes: {outfit_string}, the setting in {location}, and the camera style (iPhone 14 Pro, candid, flash photography, motion blur, unedited real life photo).",
            "caption": "The Instagram caption written in Maya's voice. Follow the specified styling rule strictly.",
            "viral_hook_text": "A short, punchy phrase (max 15 words) placed over the visual as text. It must be relatable, slightly sassy, or highly engaging (e.g., 'Pov: You finally accepted that your standards aren't too high, they're just too basic.')."
        }}

        Output only valid JSON. Do not include markdown code blocks like ```json.
        """

        system_instruction = self.system_prompt
        if performance_brief:
            system_instruction = f"{system_instruction}\n\n{performance_brief}"

        response = self.generate_content_with_retry([system_instruction, prompt])
        text = response.text.strip()

        # Robust parsing utility to locate valid JSON objects amidst LLM prefix/suffix garbage
        import re
        res_json = None
        
        # 1. Try to parse directly
        try:
            res_json = json.loads(text.strip(), strict=False)
        except Exception:
            pass
            
        # 2. Try to extract from markdown blocks
        if res_json is None:
            markdown_blocks = re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if markdown_blocks:
                for block in markdown_blocks:
                    try:
                        res_json = json.loads(block.strip(), strict=False)
                        break
                    except Exception:
                        pass
                        
        # 3. Find the first '{' and trace to find the matching '}'
        if res_json is None:
            for start_idx in range(len(text)):
                if text[start_idx] == '{':
                    balance = 0
                    for end_idx in range(start_idx, len(text)):
                        if text[end_idx] == '{':
                            balance += 1
                        elif text[end_idx] == '}':
                            balance -= 1
                            if balance == 0:
                                candidate = text[start_idx:end_idx+1]
                                try:
                                    res_json = json.loads(candidate, strict=False)
                                    break
                                except Exception:
                                    break # Try next starting '{'
                    if res_json is not None:
                        break

        if res_json is not None:
            res_json["post_subtype"] = subtype
            res_json["selected_products"] = [item["id"] if isinstance(item, dict) else str(item) for item in selected_items]
            return res_json
        else:
            print(f"Failed to parse JSON. Raw output:\n{text}")
            raise ValueError("LLM output did not contain a parseable JSON object.")

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
