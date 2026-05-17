import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Try to load .env from the current directory, or fallback to the parent dashboard directory
load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

class AgencyCOO:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        if self.api_key != "dummy_key_for_test":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

        # Central memory for the agency
        self.style_bible = [
            "Rule 1: Silent Luxury. No text on screen. Let the visuals breathe.",
            "Rule 2: Aesthetic Magnetism. Every opening frame must have a strong hook (movement, contrast, or symmetry).",
            "Rule 3: The Infinite Loop. The final frame must transition seamlessly into the first frame."
        ]

    def call_agent(self, role_prompt, task_prompt):
        """Helper to call an individual agent. If API key is dummy, mock the response for testing."""
        if self.api_key == "dummy_key_for_test":
            if "Anthropologist" in role_prompt:
                return "Visual Trend Directive:\nConcept: Match-Cut Architectural Transitions.\nColor Palette: Terra-cotta and deep emerald.\nHook: Sharp turn from a narrow cobbled street revealing a sweeping piazza."
            elif "Creative Director" in role_prompt:
                return "Storyboard:\nFrame 1 (0-1.5s): Quick pan up a 600-year-old column in Rome. High contrast.\nFrame 2 (1.5-3s): Match-cut to the model's structured blazer sleeve moving at the same speed.\nFrame 3 (3-5s): Slow-motion walking shot, no text.\nFrame 4 (5-7s): Camera pans down to the cobblestones, looping perfectly back to Frame 1."
            elif "Quality Assurance" in role_prompt:
                return "APPROVED"
            elif "Operations" in role_prompt:
                return "Asset Requirements: 4 clips total, 4K at 60fps.\nCaption: Rome isn't built in a day, but an outfit is. 🏛️✨\nAlt-text: Model in chic blazer walking in Rome piazza."

        system_instruction = f"{role_prompt}\n\nAgency Style Bible:\n" + "\n".join(self.style_bible)

        if self.model is None:
             raise ValueError("API key is invalid and mock routing failed.")

        response = self.model.generate_content([system_instruction, task_prompt])
        return response.text.strip()

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
        director_role = "You are the Creative Director. Translate concepts into frame-by-frame visual storyboards. ZERO text on screen. Focus entirely on framing, lighting, movement, and visual pacing."
        director_task = f"Based on this Directive:\n{directive}\n\nCreate a detailed frame-by-frame storyboard for a 7-second Reel. Explicitly describe the opening visual hook (0-1.5s) and the final frame transition."
        storyboard = self.call_agent(director_role, director_task)
        print(f"\n[Deliverable: Initial Storyboard]\n{storyboard}\n")

        # 3. THE CRITIC (Debate & Review Loop)
        print(">> [Critic] Reviewing against Brand Guidelines...")
        critic_role = "You are the Quality Assurance & Brand Guard. Review storyboards against the 'Silent Luxury/Aesthetic Magnetism' guidelines."
        critic_task = f"Review this storyboard:\n{storyboard}\n\nCritique it. Does it have a strong visual hook in the first 1.5s? Does the ending allow for an infinite loop? If it fails, provide specific revision notes. If it passes, reply with exactly 'APPROVED'."

        critique = self.call_agent(critic_role, critic_task)
        print(f"\n[Deliverable: Critique Notes]\n{critique}\n")

        if "APPROVED" not in critique.upper():
            print(">> [Creative Director] Revising based on Critic's feedback...")
            revision_task = f"The Critic rejected your storyboard with these notes:\n{critique}\n\nRewrite the storyboard to fix these issues. Ensure the 1.5s hook is magnetic and the loop is perfect."
            storyboard = self.call_agent(director_role, revision_task)
            print(f"\n[Deliverable: Final Approved Storyboard]\n{storyboard}\n")
        else:
            print(">> Storyboard approved on first pass.")

        # 4. THE MANAGER
        print(">> [Manager] Preparing assets and SEO metadata...")
        manager_role = "You are the Operations & Content Publisher. Handle asset management, highly optimized SEO captions, and strategic alt-text for discovery."
        manager_task = f"Based on this finalized storyboard:\n{storyboard}\n\nGenerate the Asset Requirements list for the creator. Then, draft a highly optimized SEO caption and strategic alt-text for Instagram. Remember, there is NO audio or text in the video, so metadata is critical. Start the caption with 'CAPTION: ' so it can be parsed."
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
