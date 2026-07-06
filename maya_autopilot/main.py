import os
import time
import random
from brain import MayaBrain
from media import MayaMedia
from social import MayaSocial
from agency import AgencyCOO
from analytics import StrategyOptimizer
from governance import BudgetGovernor, QualityGate

import json

class MayaAutopilot:
    def __init__(self):
        print("Initializing Maya Autopilot...")
        self.brain = MayaBrain()
        self.media = MayaMedia()
        self.social = MayaSocial()
        self.agency = AgencyCOO()
        self.optimizer = StrategyOptimizer()

        self.state_file = "state.json"
        self.locations = ["Mumbai", "Milan", "Tuscany", "Goa"]

        # Load state from file if it exists, otherwise default
        self.state = {"current_location": "Mumbai"}
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
                print(f"Loaded previous state. Location: {self.state.get('current_location')}")
            except Exception as e:
                print(f"Error loading state: {e}")

    def _save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f)
            print("Successfully saved state.")
        except Exception as e:
            print(f"Error saving state: {e}")

    def run_cycle(self, post_type="photo", force_location=None):
        """
        Runs one complete generation and posting cycle.
        """
        location = force_location if force_location else self.state.get("current_location", "Mumbai")
        print(f"\n--- Starting Autopilot Cycle ---")
        print(f"Location: {location} | Type: {post_type}")

        # Compile Algorithmic Performance Strategy Brief
        try:
            brief = self.optimizer.generate_performance_brief()
            print(f"\n[Analytics Strategy Brief Sourced]:\n{brief[:200]}...")
        except Exception as e:
            brief = ""
            print(f"[Analytics Strategy Brief Warning] {e}")

        # Load Outfit Catalog
        catalog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outfit_catalog.json")
        catalog = []
        if os.path.exists(catalog_path):
            try:
                with open(catalog_path, 'r') as f:
                    catalog = json.load(f)
            except Exception as e:
                print(f"[Autopilot Catalog Warning] Failed to load catalog: {e}")

        subtype = "lifestyle"
        selected_products = []

        if post_type == "photo":
            # 1. BRAIN: Generate Concept
            print("\n[1/4] Brain generating Photo concept...")
            governor = BudgetGovernor()
            governor.check_budget(0.001)  # LLM call budget check
            
            # Select outfit items dynamically with accessory continuity
            subtype = "lifestyle" if random.random() < 0.8 else "style_drop"
            selected_items = self._select_wardrobe(catalog, subtype)
            selected_products = [item["id"] for item in selected_items]
            
            post_data = self.brain.generate_post(
                location=location, 
                post_type=post_type, 
                performance_brief=brief, 
                selected_items=selected_items, 
                subtype=subtype
            )
            governor.record_spend(0.001)  # Record LLM call cost
            
            print(f"Prompt Generated: {post_data['image_prompt'][:100]}...")
            print(f"Caption Generated: {post_data['caption'][:50]}...")

            # 2. MEDIA: Generate Asset
            print("\n[2/4] Media generating visual assets...")
            upload_path = "maya_temp.jpg"
            max_retries = 3
            image_verified = False
            gate = QualityGate(brain=self.brain)

            for attempt in range(1, max_retries + 1):
                print(f"--- Image Generation Attempt {attempt}/{max_retries} ---")
                self.media.generate_image(post_data["image_prompt"], output_path=upload_path)

                # Verify the image quality with the Quality Gate (file checks + PIL check + Gemini Vision check)
                if gate.verify_image(upload_path):
                    image_verified = True
                    break
                else:
                    print("Discarding image and retrying...")

            if not image_verified:
                print("Warning: Max retries reached. Proceeding with the final generated image anyway.")

            # Add the Viral Text Overlay
            self.media.add_viral_text_to_image(upload_path, post_data["viral_hook_text"])
            
            # Post-overlay Quality check
            if not gate.verify_image(upload_path):
                print("[Quality Gate Warning] Image after overlay failed validation. Proceeding with caution.")
                
            caption_to_post = post_data["caption"]

        elif post_type == "reel":
            # 1. AGENCY: Multi-Agent Storyboarding for Reels
            print("\n[1/4] Agency Ecosystem generating Cinematic Reel Storyboard...")
            
            # Select outfit items dynamically with accessory continuity
            subtype = "lifestyle" if random.random() < 0.8 else "style_drop"
            selected_items = self._select_wardrobe(catalog, subtype)
            selected_products = [item["id"] for item in selected_items]
            
            outfit_descriptions = []
            for item in selected_items:
                outfit_descriptions.append(f"{item['brand']} {item['name']} ({item['visual_description']})")

            outfit_string = ", ".join(outfit_descriptions) if outfit_descriptions else "a modern silent-luxury casual high-fashion outfit curated for the setting"
            
            print(f"[80/20 Engine] Reel Selected Subtype: {subtype.upper()}")
            print(f"[80/20 Engine] Reel Outfits selected: {selected_products}")

            if subtype == "style_drop":
                concept = f"Luxury Travel & Fashion fusion concept set in {location}, featuring these retail clothes: {outfit_string}. Prompt is styled strictly around these items. Caption contains a high-engagement CTA asking followers to comment 'STYLE' to get the direct outfit details.\n\n[PAST PERFORMANCE BRIEF TO ALIGN WITH]:\n{brief}"
            else:
                concept = f"Luxury Travel & Storytelling fusion concept set in {location}, featuring this look: {outfit_string}. Prompt styles these items. Caption is a travel diary without any hard-selling, ending in an engaging lifestyle question.\n\n[PAST PERFORMANCE BRIEF TO ALIGN WITH]:\n{brief}"

            # Run the multi-agent debate to get the final storyboard and SEO metadata
            governor = BudgetGovernor()
            governor.check_budget(0.005)  # Estimate 5 LLM agent calls ($0.005)
            agency_output = self.agency.run_reel_workflow(concept)
            governor.record_spend(0.005)  # Record LLM agent calls spend

            # Extract the generated caption and viral hook
            metadata = agency_output.get("metadata", "")
            parsed_caption = ""
            parsed_hook = ""
            for line in metadata.split('\n'):
                if line.startswith("CAPTION:"):
                    parsed_caption = line.replace("CAPTION:", "").strip()
                elif line.startswith("VIRAL HOOK:"):
                    parsed_hook = line.replace("VIRAL HOOK:", "").strip()

            upload_path = "maya_temp.mp4"
            print("\n[2/4] Requesting True Cinematic Video via Muapi...")

            # Extract the actual storyboard to use as the video prompt
            storyboard_prompt = agency_output.get("storyboard", "")

            # Construct a prompt for Muapi using the strict storyboard generated by the Creative Director.
            # We strictly inject all physical identity anchors of Maya Rossi to guarantee maximum character consistency,
            # especially if the video generation falls back to generating a static image still.
            character_anchors = (
                "A highly detailed, photorealistic close-up camera shot of Maya Rossi, "
                "a 23-year-old Indian-Italian virtual influencer. Face is a 50/50 blend of young Monica Bellucci "
                "and young Deepika Padukone. Warm olive skin, signature mole on chin, deep amber eyes, "
                "messy dark brown shoulder-length bob, silent-luxury casual high-fashion outfit."
            )
            video_prompt = f"{character_anchors} Located in {location}. Candid, natural lighting, motion blur. {storyboard_prompt}"
            self.media.generate_video(video_prompt, output_path=upload_path, viral_hook_text=parsed_hook)

            # Validate video quality via Quality Gate
            gate = QualityGate(brain=self.brain)
            if not gate.verify_video(upload_path):
                raise Exception("[Quality Gate Failure] Generated video Reel did not pass verification checks!")

            if parsed_caption:
                caption_to_post = parsed_caption
            else:
                caption_to_post = f"Maya's Crew ✨ Location: {location}. #VirtualInfluencer\n(Scripted by Maya's Elite AI Agency)"

        # 3. SOCIAL: Post to Instagram
        if os.getenv("DRY_RUN", "false").lower() == "true":
            print("\n[3/4] DRY_RUN is active. Skipping Instagram Login...")
            print(f"\n[4/4] DRY_RUN is active. Skipping Publishing {post_type}...")
            print(f"Would have posted:\nCaption: {caption_to_post}\nMedia: {upload_path}")
        else:
            print("\n[3/4] Logging into Instagram...")
            self.social.login()

            print(f"\n[4/4] Publishing {post_type}...")
            if post_type == "photo":
                self.social.post_photo(upload_path, caption_to_post)
            elif post_type == "reel":
                self.social.post_reel(upload_path, caption_to_post)

        # Copy file to Next.js public/ directory so the user can download/preview it
        import shutil
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if "maya-dashboard" in current_dir:
            public_dir = os.path.join(os.path.dirname(current_dir), "public")
        else:
            public_dir = os.path.join(os.path.dirname(current_dir), "maya-dashboard", "public")
            
        os.makedirs(public_dir, exist_ok=True)
        
        media_filename = f"latest_draft.{'mp4' if post_type == 'reel' else 'jpg'}"
        public_dest = os.path.join(public_dir, media_filename)
        
        media_url = None
        if os.path.exists(upload_path):
            try:
                if os.path.exists(public_dest):
                    os.remove(public_dest)
                shutil.copy(upload_path, public_dest)
                print(f"[Autopilot] Successfully saved draft preview to public: {public_dest}")
                media_url = f"/{media_filename}?t={int(time.time())}"
            except Exception as copy_err:
                print(f"[Autopilot Warning] Failed to copy draft to public: {copy_err}")

        # Update and save State
        self.state["last_post"] = {
            "post_type": post_type,
            "location": location,
            "subtype": subtype,
            "products": selected_products,
            "timestamp": time.time(),
            "caption": caption_to_post,
            "media_url": media_url
        }

        # Record post metrics inside Analytics Feedback Loop!
        try:
            self.optimizer.record_post(
                post_type=post_type,
                location=location,
                subtype=subtype,
                products=selected_products,
                caption=caption_to_post
            )
        except Exception as e:
            print(f"[Analytics Record Error] Failed to log post: {e}")

        # Cleanup temp files
        print("\nCleaning up temporary files...")
        if os.path.exists("maya_temp.jpg"):
            os.remove("maya_temp.jpg")
        if os.path.exists("maya_temp.mp4"):
            os.remove("maya_temp.mp4")

        # Save state at the very end
        self._save_state()

        print("--- Autopilot Cycle Complete ---\n")

    def _select_wardrobe(self, catalog, subtype):
        """
        Selects outfits from catalog with accessory continuity.
        Accessories are worn 2-3 times in a row before swapping.
        """
        import random
        selected_items = []
        
        if not catalog:
            return []

        # Load previous accessories from state
        wardrobe_state = self.state.setdefault("active_wardrobe", {
            "accessories": [],
            "wear_count": 0
        })
        
        # Determine if we keep previous accessories
        keep_prev = False
        prev_accs = wardrobe_state.get("accessories", [])
        wear_count = wardrobe_state.get("wear_count", 0)
        
        # Repeat accessory 2-3 times in a row
        if prev_accs and wear_count < random.randint(2, 3):
            keep_prev = True
            wardrobe_state["wear_count"] = wear_count + 1
            print(f"[Wardrobe Selector] Repeating accessories {prev_accs} (Wear count: {wardrobe_state['wear_count']})")
        else:
            wardrobe_state["wear_count"] = 1
            wardrobe_state["accessories"] = []
            
        # Select outerwear / dress if style_drop
        if subtype == "style_drop":
            outerwear = [item for item in catalog if item["category"] in ["outerwear", "dress"]]
            if outerwear:
                selected_items.append(random.choice(outerwear))
        
        # Select accessories (repeat or select new)
        if keep_prev:
            for acc_id in prev_accs:
                for item in catalog:
                    if item["id"] == acc_id:
                        selected_items.append(item)
        else:
            accs = [item for item in catalog if item["category"] in ["accessories", "bag"]]
            if accs:
                new_acc = random.choice(accs)
                selected_items.append(new_acc)
                wardrobe_state["accessories"] = [new_acc["id"]]
                print(f"[Wardrobe Selector] Selected new accessory: {new_acc['id']}")
                
        # Save state changes immediately
        self._save_state()
        
        return selected_items

    def travel(self):
        """Randomly decides to travel to a new location."""
        current = self.state.get("current_location", "Mumbai")
        new_location = random.choice([loc for loc in self.locations if loc != current])
        print(f"Maya is traveling from {current} to {new_location} ✈️")
        self.state["current_location"] = new_location
        self._save_state()

if __name__ == "__main__":
    autopilot = MayaAutopilot()

    print("Welcome to Maya Rossi's True Autopilot.")
    print("Checking environment variables and initiating cycle...")

    # Choose randomly between a photo and a reel for variety
    post_choice = random.choice(["photo", "photo", "reel"])

    try:
        # Occasionally travel to keep the content dynamic
        if random.random() < 0.2: # 20% chance to travel
            autopilot.travel()

        autopilot.run_cycle(post_type=post_choice)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"CRITICAL ERROR in Autopilot Execution:\n{error_trace}")
        # In a CI/CD environment like GitHub actions, we want it to exit with an error code
        # so you get an email notification if it fails.
        import sys
        sys.exit(1)
