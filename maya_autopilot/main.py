import os
import time
import random
from brain import MayaBrain
from media import MayaMedia
from social import MayaSocial

class MayaAutopilot:
    def __init__(self):
        print("Initializing Maya Autopilot...")
        self.brain = MayaBrain()
        self.media = MayaMedia()
        self.social = MayaSocial()

        # Internal state to track location, to prevent "teleporting"
        self.current_location = "Mumbai"
        self.locations = ["Mumbai", "Milan", "Tuscany", "Goa"]

    def run_cycle(self, post_type="photo", force_location=None):
        """
        Runs one complete generation and posting cycle.
        """
        location = force_location if force_location else self.current_location
        print(f"\n--- Starting Autopilot Cycle ---")
        print(f"Location: {location} | Type: {post_type}")

        # 1. BRAIN: Generate Concept
        print("\n[1/4] Brain generating post concept...")
        post_data = self.brain.generate_post(location=location, post_type=post_type)
        print(f"Prompt Generated: {post_data['image_prompt'][:100]}...")
        print(f"Caption Generated: {post_data['caption'][:50]}...")

        # 2. MEDIA: Generate Image
        print("\n[2/4] Media generating visual assets...")
        image_path = "maya_temp.jpg"
        self.media.generate_image(post_data["image_prompt"], output_path=image_path)

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

        print("--- Autopilot Cycle Complete ---\n")

    def travel(self):
        """Randomly decides to travel to a new location."""
        new_location = random.choice([loc for loc in self.locations if loc != self.current_location])
        print(f"Maya is traveling from {self.current_location} to {new_location} ✈️")
        self.current_location = new_location
        # A real implementation would force the next post to be an airport/travel post

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
