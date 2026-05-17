import os
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from dotenv import load_dotenv

load_dotenv()

class MayaSocial:
    def __init__(self):
        self.username = os.getenv("IG_USERNAME")
        self.password = os.getenv("IG_PASSWORD")
        self.cl = Client()
        self.session_file = "ig_session.json"

        if not self.username or not self.password:
            raise ValueError("IG_USERNAME or IG_PASSWORD not found in environment variables.")

    def login(self):
        """
        Handles logging into Instagram. Reuses session if possible to avoid flags.
        """
        try:
            # Try to load previous session
            if os.path.exists(self.session_file):
                self.cl.load_settings(self.session_file)
                self.cl.login(self.username, self.password)
                # Check if session is valid
                self.cl.get_timeline_feed()
                print("Successfully logged in using saved session.")
            else:
                self.cl.login(self.username, self.password)
                self.cl.dump_settings(self.session_file)
                print("Logged in and saved new session.")
        except LoginRequired:
            print("Session expired. Re-logging in...")
            self.cl.login(self.username, self.password)
            self.cl.dump_settings(self.session_file)
            print("Logged in and saved new session.")
        except Exception as e:
            print(f"Failed to log in to Instagram: {e}")
            raise e

    def post_photo(self, photo_path, caption):
        """
        Uploads a photo to the feed.
        """
        print(f"Uploading photo {photo_path}...")
        try:
            media = self.cl.photo_upload(photo_path, caption)
            print(f"Successfully posted photo! Media ID: {media.pk}")
            return media.pk
        except Exception as e:
            print(f"Failed to upload photo: {e}")
            raise e

    def post_reel(self, video_path, caption):
        """
        Uploads a reel to Instagram.
        """
        print(f"Uploading reel {video_path}...")
        try:
            media = self.cl.clip_upload(video_path, caption)
            print(f"Successfully posted reel! Media ID: {media.pk}")
            return media.pk
        except Exception as e:
            print(f"Failed to upload reel: {e}")
            raise e

if __name__ == "__main__":
    # Test the Social module initialization
    try:
        social = MayaSocial()
        print("Social module initialized.")
        # social.login()
        # social.post_photo("test_image.jpg", "Hello world from Autopilot. #VirtualInfluencer")
    except Exception as e:
        print(f"Social Module Error: {e}")
