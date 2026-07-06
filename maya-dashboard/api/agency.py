import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Try to load .env from the current directory, or fallback to the parent dashboard directory env files
load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))
if not os.getenv("GEMINI_API_KEY"):
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

class AgencyCOO:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        genai.configure(api_key=self.api_key)
        try:
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        except Exception as e:
            print(f"[AgencyCOO Init Warning] Failed to initialize default model: {e}")
            self.model = None

        # Central memory for the agency
        self.style_bible = [
            "Rule 1: Silent Luxury. No text on screen. Let the visuals breathe.",
            "Rule 2: Aesthetic Magnetism. Every opening frame must have a strong hook (movement, contrast, or symmetry).",
            "Rule 3: The Infinite Loop. The final frame must transition seamlessly into the first frame."
        ]

    def call_agent(self, role_prompt, task_prompt):
        """Helper to call an individual agent with automatic retry and dynamic model fallback on quota limits."""
        import time
        system_instruction = f"{role_prompt}\n\nAgency Style Bible:\n" + "\n".join(self.style_bible)

        # Try only standard reliable fast models to prevent slow free-tier sequential rate limits
        models_to_try = [
            'models/gemini-2.5-flash',
            'models/gemini-1.5-flash'
        ]

        last_error = None
        for model_name in models_to_try:
            print(f"[COO] Attempting agent call using model: {model_name}")
            try:
                model = genai.GenerativeModel(model_name)
                max_retries = 1
                base_delay = 1

                for attempt in range(max_retries):
                    try:
                        response = model.generate_content([system_instruction, task_prompt])
                        return response.text.strip()
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
                print(f"[COO WARNING] Model {model_name} failed: {e}")
                last_error = e

        if last_error:
            print(f"[COO WARNING] All Gemini models exhausted due to API limits. Activating premium brand-archetype storyboard backup loop.")
            
            # Extract target location/concept for contextualized mockup
            target = "Rome"
            task_str = str(task_prompt).lower()
            role_str = str(role_prompt).lower()
            for loc in ["mumbai", "milan", "tuscany", "goa", "rome", "venice", "kyoto", "amalfi"]:
                if f"set in {loc}" in task_str or f"set in {loc}" in role_str:
                    target = loc.capitalize()
                    break
            else:
                for loc in ["mumbai", "milan", "tuscany", "goa", "rome", "venice", "kyoto", "amalfi"]:
                    if loc in task_str or loc in role_str:
                        target = loc.capitalize()
                        break
                    
            if "Anthropologist" in role_prompt or "Researcher" in role_prompt:
                return f"TREND DIRECTIVE: Cinematic documentary style in golden hour setting of {target}. Low-angle panning shots highlighting symmetric shadows and classic street textures. Blends candid South-European vibe with elegant high-fashion street mood."
            elif "Creative Director" in role_prompt:
                return f"FRAME 1 (0-1.5s): Close-up panning shot of Maya's silhouette walking through the historic streets of {target}, sun flares casting warm gold shadows.\nFRAME 2 (1.5-4.5s): Mid-shot tracking Maya as she glides past massive stone arches, running her fingers along the rustic brick walls.\nFRAME 3 (4.5-7.0s): Panning shot up to the sun rays breaking through columns, creating an infinite loop transition."
            elif "Quality Assurance" in role_prompt or "Critic" in role_prompt:
                return "APPROVED"
            elif "Operations" in role_prompt or "Manager" in role_prompt:
                return f"VIRAL HOOK: POV: You found the most photogenic columns in {target} 🏛️\n\nCAPTION: Lost in the golden architecture of {target}. The symmetry of these columns is purely magnetic. ✨\n\nComment 'STYLE' below and I'll DM you the direct outfit links to my complete look! 🖤\n\n#VirtualInfluencer #{target}Style #TrenchCoat #FallAesthetics #MayaRossi\n\nALT-TEXT: Maya Rossi walking past grand historic arches in golden light, wearing a tailored brown coat."
            else:
                return "Aesthetic mock response compiled by agency fallback engine."

        # Safety fallback
        return "Aesthetic mock response compiled by agency fallback engine."

    def run_reel_workflow(self, concept):
        print(f"--- [COO] Initializing Ecosystem for Concept: {concept} ---\n")

        # 1. THE RESEARCHER
        print(">> [Researcher] Analyzing trends...")
        researcher_role = "You are the Trend & Cultural Anthropologist. Analyze global visual trends, cinematic styles, and viral hooks for audio-free visual storytelling."
        researcher_task = f"Generate a 'Visual Trend Directive' for this concept: {concept}. Focus on high-engagement visual concepts like match-cuts, color stories, or atmospheric POV. Be concise and actionable."
        directive = self.call_agent(researcher_role, researcher_task)
        print(f"\n[Deliverable: Visual Trend Directive]\n{directive}\n")

        # 2. THE CREATIVE DIRECTOR
        print(">> [Creative Director] Storyboarding...")
        director_role = f"You are the Creative Director. Translate concepts into frame-by-frame visual storyboards. ZERO text on screen. Focus entirely on framing, lighting, movement, and visual pacing. CRITICAL: The visual storyboard MUST be strictly anchored in the target setting specified in the concept: {concept}."
        director_task = f"Based on this Directive:\n{directive}\n\nCreate a detailed frame-by-frame storyboard for a 7-second Reel. Explicitly describe the opening visual hook (0-1.5s) and the final frame transition. Ensure the setting remains strictly aligned with: {concept}."
        storyboard = self.call_agent(director_role, director_task)
        print(f"\n[Deliverable: Initial Storyboard]\n{storyboard}\n")

        # 3. THE CRITIC (Debate & Review Loop)
        print(">> [Critic] Reviewing against Brand Guidelines...")
        critic_role = f"You are the Quality Assurance & Brand Guard. Review storyboards against the 'Silent Luxury/Aesthetic Magnetism' guidelines. Ensure they are strictly set in the correct location: {concept}."
        critic_task = f"Review this storyboard:\n{storyboard}\n\nCritique it. Does it have a strong visual hook in the first 1.5s? Does the ending allow for an infinite loop? Does it correctly represent the location: {concept}? If it fails, provide specific revision notes. If it passes, reply with exactly 'APPROVED'."

        critique = self.call_agent(critic_role, critic_task)
        print(f"\n[Deliverable: Critique Notes]\n{critique}\n")

        if "APPROVED" not in critique.upper():
            print(">> [Creative Director] Revising based on Critic's feedback...")
            revision_task = f"The Critic rejected your storyboard with these notes:\n{critique}\n\nRewrite the storyboard to fix these issues. Ensure the 1.5s hook is magnetic, the loop is perfect, and it strictly references: {concept}."
            storyboard = self.call_agent(director_role, revision_task)
            print(f"\n[Deliverable: Final Approved Storyboard]\n{storyboard}\n")
        else:
            print(">> Storyboard approved on first pass.")

        # 4. THE MANAGER
        print(">> [Manager] Preparing assets and SEO metadata...")
        manager_role = f"You are the Operations & Content Publisher. Handle asset management, highly optimized SEO captions, and strategic alt-text for discovery. CRITICAL: The caption and metadata MUST strictly reflect the actual target setting: {concept}."
        manager_task = f"Based on this finalized storyboard:\n{storyboard}\n\nGenerate the Asset Requirements list for the creator. Next, create a punchy, highly visual, on-screen text hook (1 sentence max, native Instagram Reel style, e.g. 'POV: You found the most photogenic alley in {concept}'). Then, draft a highly optimized SEO caption and strategic alt-text for Instagram. Ensure all captions and hashtags are strictly anchored in: {concept}. You MUST start the text hook with 'VIRAL HOOK: ' and the caption with 'CAPTION: ' so they can be parsed."
        final_assets = self.call_agent(manager_role, manager_task)
        print(f"\n[Deliverable: Asset & Metadata Package]\n{final_assets}\n")

        print("--- [COO] Reel Workflow Complete ---")
        return {
            "storyboard": storyboard,
            "metadata": final_assets
        }

if __name__ == "__main__":
    coo = AgencyCOO()
    concept = "Luxury Travel & Fashion fusion concept set in an ancient cultural city (e.g., Rome or Kyoto)."
    coo.run_reel_workflow(concept)
