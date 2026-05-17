import os
import time
import random
from brain import MayaBrain
from media import MayaMedia
from social import MayaSocial

import json

class MayaAutopilot:
    def __init__(self):
        print("Initializing Maya Autopilot...")
        self.brain = MayaBrain()
        self.media = MayaMedia()
        self.social = MayaSocial()

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

        # 1. BRAIN: Generate Concept
        print("\n[1/4] Brain generating post concept...")
        post_data = self.brain.generate_post(location=location, post_type=post_type)
        print(f"Prompt Generated: {post_data['image_prompt'][:100]}...")
        print(f"Caption Generated: {post_data['caption'][:50]}...")
        print(f"Viral Hook: {post_data['viral_hook_text']}")

        # 2. MEDIA: Generate Image with Verification Loop
        print("\n[2/4] Media generating visual assets...")
        image_path = "maya_temp.jpg"

        max_retries = 3
        image_verified = False

        for attempt in range(1, max_retries + 1):
            print(f"--- Generation Attempt {attempt}/{max_retries} ---")
            self.media.generate_image(post_data["image_prompt"], output_path=image_path)

            # Verify the image quality with the Brain
            if self.brain.verify_image(image_path):
                image_verified = True
                break
            else:
                print("Discarding image and retrying...")

        if not image_verified:
            print("Warning: Max retries reached. Proceeding with the final generated image anyway.")


        # Add the Viral Text Overlay
        self.media.add_viral_text_to_image(image_path, post_data["viral_hook_text"])

        # 3. PREPARE MEDIA FOR UPLOAD
        upload_path = image_path
        if post_type == "reel":
            print("\n[2.5/4] Converting Image to Reel format...")
            video_path = "maya_temp.mp4"
            upload_path = self.media.create_reel_from_image(image_path, output_path=video_path)

        # 4. SOCIAL: Post to Instagram
        print("\n[3/4] Logging into Instagram...")
        self.social.login()

        print(f"\n[4/4] Publishing {post_type}...")
        if post_type == "photo":
            self.social.post_photo(upload_path, post_data["caption"])
        elif post_type == "reel":
            self.social.post_reel(upload_path, post_data["caption"])

        # Cleanup temp files
        print("\nCleaning up temporary files...")
        if os.path.exists("maya_temp.jpg"):
            os.remove("maya_temp.jpg")
        if os.path.exists("maya_temp.mp4"):
            os.remove("maya_temp.mp4")

        # Save state at the very end
        self._save_state()

        print("--- Autopilot Cycle Complete ---\n")

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
        print(f"Autopilot encountered a critical error during execution: {e}")
        # In a CI/CD environment like GitHub actions, we want it to exit with an error code
        # so you get an email notification if it fails.
        import sys
        sys.exit(1)
