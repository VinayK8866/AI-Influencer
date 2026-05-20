import os
import sys
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    FeedbackRequired,
    PleaseWaitFewMinutes,
    PhotoNotUpload,
    VideoNotUpload,
    ClipNotUpload
)
from dotenv import load_dotenv

load_dotenv()

class MayaSocial:
    def __init__(self):
        self.username = os.getenv("IG_USERNAME")
        self.password = os.getenv("IG_PASSWORD")
        self.cl = Client()
        tmp_dir = "/tmp" if os.environ.get("VERCEL") else "."
        self.session_file = os.path.join(tmp_dir, "ig_session.json")

        if not self.username or not self.password:
            raise ValueError("IG_USERNAME or IG_PASSWORD not found in environment variables.")

        # Configure proxy if available
        self.proxy = os.getenv("IG_PROXY")
        if self.proxy:
            print(f"Configuring Instagram proxy: {self.proxy}")
            self.cl.set_proxy(self.proxy)

    def handle_exception(self, e, action_name):
        """
        Intercepts common Instagram/instagrapi errors to print beautiful,
        highly actionable developer guides for recovery.
        """
        err_msg = str(e).lower()
        is_challenge = isinstance(e, ChallengeRequired) or "challenge_required" in err_msg
        is_feedback = isinstance(e, (FeedbackRequired, PleaseWaitFewMinutes)) or "feedback_required" in err_msg or "please_wait" in err_msg
        
        print(f"Failed during {action_name}: {e}")
        
        if is_challenge:
            print("\n" + "="*80)
            print("🚨 INSTAGRAM SECURITY CHALLENGE DETECTED 🚨")
            print("Instagram is demanding manual verification (SMS, Email, or Selfie verification).")
            
            is_ci = os.environ.get("GITHUB_ACTIONS") or os.environ.get("CI")
            if is_ci:
                print("\n[GitHub Actions / CI/CD Runner Detected]")
                print("Because the script is running in a non-interactive datacenter container:")
                print("1. Log in to the Instagram account manually on a real device (phone/browser).")
                print("2. Solve the challenge as requested by Instagram.")
                print("3. Perform a quick interaction (like a photo or a post) to solidify the login.")
                print("4. Copy the contents of the generated 'ig_session.json' file from your local workspace.")
                print("5. Base64-encode it (run: cat ig_session.json | base64 -w 0).")
                print("6. Go to your GitHub Repository -> Settings -> Secrets and variables -> Actions.")
                print("7. Update the 'IG_SESSION_BASE64' secret with the base64-encoded string.")
                print("\n💡 RECOMMENDED STRATEGY TO PREVENT CHALLENGES:")
                print("Add a residential or mobile proxy secret called 'IG_PROXY' (e.g. http://user:pass@host:port).")
                print("Using a consistent proxy avoids the 'New IP / Datacenter' warning flag entirely.")
            else:
                print("\n[Local/Interactive Environment Detected]")
                print("To clear this challenge:")
                print("1. Please log in manually on your physical phone or web browser.")
                print("2. Solve the challenge prompts there.")
                print("3. Alternatively, configure a high-quality residential/mobile proxy via 'IG_PROXY' in your .env.")
            print("="*80 + "\n")
            
        elif is_feedback:
            print("\n" + "="*80)
            print("⏳ INSTAGRAM TEMPORARY ACTION BLOCK ⏳")
            print("Instagram has flagged automated requests and issued an action limit.")
            print("Please pause the autopilot for 24-48 hours to let the account reputation recover.")
            print("="*80 + "\n")
            
        raise e

    def login(self):
        """
        Handles logging into Instagram. Reuses session if possible to avoid bot detection.
        """
        try:
            if os.path.exists(self.session_file):
                # Clean up corrupted/empty session files
                if os.path.getsize(self.session_file) < 10:
                    print(f"Session file {self.session_file} is empty or corrupted. Removing to start fresh...")
                    try:
                        os.remove(self.session_file)
                    except Exception:
                        pass
                else:
                    print(f"Loading saved session from {self.session_file}...")
                    try:
                        self.cl.load_settings(self.session_file)
                        # Test session validity by making a quick public/private request
                        self.cl.get_timeline_feed()
                        print("Successfully logged in using saved session (bypass credentials).")
                        return
                    except Exception as session_err:
                        print(f"Saved session is invalid/expired: {session_err}. Proceeding with fresh login...")
                        try:
                            os.remove(self.session_file)
                        except Exception:
                            pass

            # If no session file exists or it has expired, perform full credential login
            print("Performing fresh credential login...")
            self.cl.login(self.username, self.password)
            self.cl.dump_settings(self.session_file)
            print("Successfully logged in and saved new session.")
        except Exception as e:
            self.handle_exception(e, "Instagram login")

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
            self.handle_exception(e, f"photo upload ({photo_path})")

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
            self.handle_exception(e, f"reel upload ({video_path})")

if __name__ == "__main__":
    # Test the Social module initialization
    try:
        social = MayaSocial()
        print("Social module initialized.")
        # social.login()
        # social.post_photo("test_image.jpg", "Hello world from Autopilot. #VirtualInfluencer")
    except Exception as e:
        print(f"Social Module Error: {e}")
