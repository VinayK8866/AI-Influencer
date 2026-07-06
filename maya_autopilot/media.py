import os
import io
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class MayaMedia:
    def __init__(self):
        self.muapi_api_key = os.getenv("MUAPI_API_KEY")

        # We now prefer Muapi.ai for high-fidelity video/image generation, keeping HF as fallback
        if not self.muapi_api_key:
            print("Warning: MUAPI_API_KEY not found, falling back to legacy HF pipeline if available.")
            self.api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
            self.headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
        else:
            self.api_url = "https://api.muapi.ai/api/v1"
            self.headers = {
                "x-api-key": self.muapi_api_key,
                "Content-Type": "application/json"
            }

    def generate_video(self, prompt, output_path="output.mp4"):
        """
        Uses Muapi's async polling architecture to generate a high-quality video (e.g., using Seedance).
        """
        if not self.muapi_api_key:
            raise Exception("Cannot generate true video without MUAPI_API_KEY.")

        import time
        print(f"\n[Muapi] Requesting Video Generation. Prompt: {prompt[:100]}...")

        # We will attempt multiple common video endpoints.
        endpoints_to_try = [
            f"{self.api_url}/seedance-pro-t2v",
            f"{self.api_url}/kling-v2.1-master-t2v",
            f"{self.api_url}/kling-v3.0-standard-text-to-video",
            f"{self.api_url}/runway-text-to-video",
            f"{self.api_url}/wan2.1-text-to-video",
            f"{self.api_url}/veo3-fast-text-to-video",
            f"{self.api_url}/seedance-lite-t2v"
        ]

        submit_res = None
        payload = {
            "prompt": prompt,
            "duration": 5,
            "aspect_ratio": "9:16" # Perfect for Instagram Reels
        }

        try:
            for endpoint in endpoints_to_try:
                print(f"[Muapi] Trying direct path: {endpoint}...")
                submit_res = requests.post(endpoint, headers=self.headers, json=payload)

                if submit_res.status_code in [200, 202]:
                    print(f"[Muapi] Successfully submitted job to {endpoint}.")
                    break
                else:
                    print(f"[Muapi] Endpoint failed: {submit_res.status_code} - {submit_res.text}")
                    submit_res = None

            if not submit_res:
                raise Exception("All attempted Muapi paths returned errors or 404s.")

            data = submit_res.json()
            request_id = data.get("request_id")

            if not request_id:
                raise Exception("No request_id returned from Muapi.")

            print(f"[Muapi] Job submitted successfully. Request ID: {request_id}")

            # Step 2: Poll for completion
            poll_endpoint = f"{self.api_url}/predictions/{request_id}/result"

            max_attempts = 60 # Poll for up to 10 minutes (10s intervals)
            for attempt in range(max_attempts):
                time.sleep(10)
                print(f"[Muapi] Polling for video completion... (Attempt {attempt+1}/{max_attempts})")

                poll_res = requests.get(poll_endpoint, headers=self.headers)
                if poll_res.status_code != 200:
                    continue

                poll_data = poll_res.json()
                status = poll_data.get("status")

                if status == "completed":
                    video_url = poll_data.get("output_url") or poll_data.get("video_url")
                    if not video_url:
                        raise Exception("Job completed but no video URL found in response.")

                    print(f"[Muapi] Video generation complete! Downloading from {video_url}...")

                    # Download the video file
                    video_data = requests.get(video_url)
                    with open(output_path, "wb") as f:
                        f.write(video_data.content)

                    print(f"[Muapi] Video saved to {output_path}")
                    return output_path

                elif status in ["failed", "error"]:
                    raise Exception(f"Muapi video generation failed: {poll_data}")

            raise Exception("Muapi video generation timed out.")

        except Exception as e:
            print(f"\n[CRITICAL] Video Generation Failed: {e}")
            print("[FALLBACK] Automatically generating high-fidelity static image first to maintain facial consistency...")
            fallback_jpg_path = output_path.replace(".mp4", ".jpg")
            self.generate_image(prompt, output_path=fallback_jpg_path)

            # Option A: Attempt to animate static image via public Hugging Face ZeroGPU Space
            try:
                print("[FALLBACK] [Option A] Attempting to animate static image via Hugging Face Space (multimodalart/wan2-1-fast)...")
                from gradio_client import Client, handle_file
                import shutil
                
                client = Client("multimodalart/wan2-1-fast", timeout=12)
                print("[FALLBACK] [Option A] Submitting to Wan2.1 Space...")
                
                result = client.predict(
                    input_image=handle_file(fallback_jpg_path),
                    prompt="candid cinematic video, beautiful virtual influencer smiling, dynamic face motion, slow camera pan",
                    height=512,
                    width=896,
                    negative_prompt="Bright tones, overexposed, static, blurred details, low quality, watermark, text",
                    duration_seconds=2,
                    guidance_scale=5.0,
                    steps=10,
                    seed=42,
                    randomize_seed=True,
                    api_name="/generate_video"
                )
                
                if isinstance(result, tuple) and len(result) > 0:
                    video_info = result[0]
                    video_path = video_info.get("video") if isinstance(video_info, dict) else video_info
                    if video_path and os.path.exists(video_path):
                        shutil.copy(video_path, output_path)
                        print(f"[FALLBACK] [Option A] Successfully animated video using HF Space and saved to {output_path}!")
                        return output_path
                raise Exception("Invalid result structure from Hugging Face Space.")
            except Exception as hf_err:
                print(f"[FALLBACK] [Option A Info] Hugging Face Space queue busy or timed out ({hf_err}). Swapping seamlessly to local dynamic engine...")

            print("[FALLBACK] Converting fallback image to Reel format via local cinematic engine...")
            return self.create_reel_from_image(fallback_jpg_path, output_path=output_path)

    def generate_image(self, prompt, output_path="output.jpg"):
        """
        Calls Muapi (or fallback HF) to generate an image based on the prompt.
        """
        import time
        print(f"Generating image with prompt: {prompt}")

        # Try Muapi first if API key is set
        if self.muapi_api_key:
            print("[Muapi] Generating high-fidelity image...")
            image_endpoints = [
                f"{self.api_url}/flux-dev",
                f"{self.api_url}/flux-schnell",
                f"{self.api_url}/midjourney-v7",
                f"{self.api_url}/midjourney-v8"
            ]
            payload = {
                "prompt": prompt,
                "num_images": 1,
                "width": 1024,
                "height": 1024
            }

            for endpoint in image_endpoints:
                try:
                    print(f"[Muapi] Trying direct path: {endpoint}...")
                    response = requests.post(endpoint, headers=self.headers, json=payload)
                    if response.status_code in [200, 202]:
                        data = response.json()
                        request_id = data.get("request_id")
                        if request_id:
                            print(f"[Muapi] Image job submitted successfully. Request ID: {request_id}")
                            
                            # Poll for image completion
                            poll_endpoint = f"{self.api_url}/predictions/{request_id}/result"
                            max_attempts = 30 # Poll for up to 5 minutes (10s intervals)
                            for attempt in range(max_attempts):
                                time.sleep(10)
                                print(f"[Muapi] Polling for image completion... (Attempt {attempt+1}/{max_attempts})")
                                
                                poll_res = requests.get(poll_endpoint, headers=self.headers)
                                if poll_res.status_code != 200:
                                    continue
                                
                                poll_data = poll_res.json()
                                status = poll_data.get("status")
                                
                                if status == "completed":
                                    image_url = poll_data.get("output_url") or poll_data.get("image_url")
                                    if not image_url and poll_data.get("outputs"):
                                        image_url = poll_data.get("outputs")[0]
                                    
                                    if image_url:
                                        print(f"[Muapi] Image generation complete! Downloading from {image_url}...")
                                        img_res = requests.get(image_url)
                                        with open(output_path, "wb") as f:
                                            f.write(img_res.content)
                                        print(f"[Muapi] Image successfully saved to {output_path}")
                                        return output_path
                                    else:
                                        print("[Muapi] Job completed but no image URL found in response.")
                                        break
                                elif status in ["failed", "error"]:
                                    print(f"[Muapi] Image generation failed on {endpoint}: {poll_data}")
                                    break
                        else:
                            print(f"[Muapi] No request_id returned from {endpoint}")
                    else:
                        print(f"[Muapi] Endpoint {endpoint} failed: {response.status_code} - {response.text}")
                except Exception as ex:
                    print(f"[Muapi] Error generating image via {endpoint}: {ex}")

            print("[Muapi] Muapi image generation failed. Falling back to Hugging Face...")

        # For fallback, we use Hugging Face with a resilient multi-model fallback loop
        hf_key = os.getenv("HF_API_KEY")
        if not hf_key:
            raise Exception("Cannot generate fallback image. HF_API_KEY is missing from environment variables.")

        fallback_models = [
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/stable-diffusion-2-1",
            "runwayml/stable-diffusion-v1-5"
        ]

        last_error = None
        for model in fallback_models:
            print(f"[FALLBACK] Attempting Hugging Face generation with model: {model}")
            url = f"https://router.huggingface.co/hf-inference/models/{model}"

            if "flux" in model.lower():
                payload = {"inputs": prompt}
            else:
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "negative_prompt": "ugly, blurry, deformed, poorly drawn, AI-perfect, weird hands, extra limbs, cartoon, 3d render, artificial lighting",
                        "num_inference_steps": 50,
                        "guidance_scale": 7.5
                    }
                }

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, headers={"Authorization": f"Bearer {hf_key}"}, json=payload)

                    if response.status_code == 200:
                        image = Image.open(io.BytesIO(response.content))
                        image.save(output_path)
                        print(f"Image successfully generated via Hugging Face ({model}) and saved to {output_path}")
                        return output_path
                    elif response.status_code == 503:
                        print(f"Model {model} is loading (Attempt {attempt+1}/{max_retries}). Waiting 20 seconds...")
                        time.sleep(20)
                    else:
                        print(f"Model {model} returned status {response.status_code}: {response.text}")
                        last_error = Exception(f"Failed to generate image via {model}: {response.status_code} - {response.text}")
                        break
                except Exception as e:
                    print(f"Error on {model} (Attempt {attempt+1}): {e}")
                    last_error = e
                    time.sleep(5)

            print(f"[FALLBACK] Model {model} failed. Trying next model...")

        if os.getenv("DRY_RUN", "false").lower() == "true":
            print("\n⚠️  [DRY_RUN] Image generation APIs failed or unauthorized. Creating a solid color mock test image for local verification...")
            self.create_mock_image(output_path, text=prompt)
            return output_path

        if last_error:
            raise last_error
        raise Exception("All Hugging Face fallback models failed to generate the image.")

    def create_mock_image(self, output_path="output.jpg", text="Mock Asset"):
        """
        Generates a standard test image for local development and verification.
        """
        from PIL import ImageDraw
        print(f"[MOCK] Rendering local mock image asset: {output_path}")
        img = Image.new('RGB', (1024, 1024), color=(33, 37, 43))
        draw = ImageDraw.Draw(img)
        
        # Simple aesthetic borders and text center
        draw.rectangle([(50, 50), (974, 974)], outline=(255, 198, 10), width=4)
        draw.text((100, 480), f"MAYA AUTOPILOT\n[DRY_RUN ACTIVE]\n\nPrompt Preview:\n{text[:80]}...", fill=(255, 255, 255))
        img.save(output_path)
        print(f"[MOCK] Mock image successfully saved to {output_path}")
        return output_path


    def add_viral_text_to_image(self, image_path, text):
        """
        Mimics Instagram's native text overlays by drawing the viral hook directly onto the image.
        """
        from PIL import ImageDraw, ImageFont
        import textwrap

        print(f"Adding viral text overlay to {image_path}")
        # Convert base image to RGBA to support transparency
        image = Image.open(image_path).convert("RGBA")

        # Create a blank transparent image for the overlay
        overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # We wrap the text so it doesn't run off the edges
        # Assuming typical SDXL resolution of 1024x1024
        wrapped_text = textwrap.fill(text, width=30)

        # Ensure a readable font exists, download Roboto if necessary
        font_path = "Roboto-Bold.ttf"
        if not os.path.exists(font_path):
            import urllib.request
            print("Downloading Roboto font for text overlays...")
            try:
                urllib.request.urlretrieve(
                    "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf",
                    font_path
                )
            except Exception as e:
                print(f"Failed to download font: {e}")

        try:
            font = ImageFont.truetype(font_path, 45)
        except IOError:
            # Absolute fallback if download fails
            print("Warning: Could not load TTF font, falling back to default.")
            font = ImageFont.load_default()

        # Add a semi-transparent black background behind the text for readability
        # Calculate bounding box using textbbox
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center horizontally, place somewhat centrally/lower-middle vertically
        img_width, img_height = image.size
        x = (img_width - text_width) / 2
        y = img_height * 0.4

        # Draw background rectangle on the transparent overlay
        padding = 20
        draw.rectangle(
            [(x - padding, y - padding), (x + text_width + padding, y + text_height + padding)],
            fill=(0, 0, 0, 160)
        )

        # Draw text on the transparent overlay
        draw.multiline_text((x, y), wrapped_text, font=font, fill=(255, 255, 255), align="center")

        # Composite the overlay onto the base image
        out = Image.alpha_composite(image, overlay)
        # Convert back to RGB for saving as JPEG
        out = out.convert("RGB")
        out.save(image_path)
        return image_path

    def download_background_music(self, vibe="random"):
        """
        Downloads and caches a dynamic rotation of high-quality, copyright-safe background tracks.
        Hits the live Jamendo CC-Music API to retrieve thousands of diverse electronic/chill tracks.
        Falls back to a curated robust list of stable tracks if the API is offline or rate-limited.
        """
        import urllib.request
        import random
        import json
        import os

        music_dir = "assets"
        os.makedirs(music_dir, exist_ok=True)

        # 1. Try fetching from live Jamendo CC-licensed music API for massive variety
        try:
            # Sourced via public CC developer Client ID (completely free & open search)
            api_url = "https://api.jamendo.com/v3.0/tracks/?client_id=56d30c95&format=json&limit=30&tags=electronic,house,lounge,chill&audioformat=mp32"
            print("[Music API] Querying Jamendo API for trending copyright-safe beats...")
            
            req = urllib.request.Request(
                api_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                api_data = json.loads(response.read().decode('utf-8'))
                results = api_data.get("results", [])
                
                if results:
                    selected_track = random.choice(results)
                    track_id = selected_track.get("id")
                    track_name = selected_track.get("name")
                    audio_url = selected_track.get("audio")
                    
                    if audio_url:
                        music_path = os.path.join(music_dir, f"jamendo_{track_id}.mp3")
                        if not os.path.exists(music_path):
                            print(f"[Music API] Downloading '{track_name}' (ID: {track_id}) dynamically...")
                            down_req = urllib.request.Request(
                                audio_url, 
                                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                            )
                            with urllib.request.urlopen(down_req, timeout=12) as down_res, open(music_path, 'wb') as out_file:
                                out_file.write(down_res.read())
                            print(f"[Music API] Successfully cached and set dynamic track: '{track_name}'")
                        return music_path
        except Exception as api_err:
            print(f"[Music API Warning] Jamendo CC API issue ({api_err}). Swapping to cached fallbacks...")

        # 2. Curated Bulletproof fallback playlist (16 stable direct-download tracks)
        playlist = [
            f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{i}.mp3" for i in range(1, 17)
        ]
        selected_fallback = random.choice(playlist)
        song_num = selected_fallback.split("-")[-1].replace(".mp3", "")
        music_path = os.path.join(music_dir, f"bg_music_fallback_{song_num}.mp3")
        
        if not os.path.exists(music_path):
            print(f"[Music Fallback] Downloading cached synth track {song_num}...")
            try:
                req = urllib.request.Request(
                    selected_fallback, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=10) as response, open(music_path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"[Music Fallback] Successfully cached track {song_num}")
            except Exception as e:
                print(f"[Music Warning] Could not retrieve fallback track: {e}")
                # Ultimate fallback: return any existing mp3 file in the directory
                existing = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.endswith(".mp3")]
                if existing:
                    return random.choice(existing)
                return None
        return music_path

    def create_reel_from_image(self, image_path, output_path="output.mp4"):
        """
        Creates a basic "Reel" (short video) from a static image.
        For a completely free tier without API limits, we use moviepy to make a panning/zooming
        effect on the image to simulate motion.
        """
        # Patch PIL.Image.ANTIALIAS for compatibility with modern PIL versions inside moviepy
        try:
            import PIL.Image
            if not hasattr(PIL.Image, 'ANTIALIAS'):
                PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
        except Exception:
            pass

        from moviepy.editor import ImageClip

        print(f"Converting image {image_path} to Reel {output_path}")

        # Load the image
        clip = ImageClip(image_path)
        
        # Enforce even dimensions to prevent FFmpeg stride and pixel format alignment glitches
        W, H = clip.size
        even_w = W - (W % 2)
        even_h = H - (H % 2)
        if even_w != W or even_h != H:
            print(f"[Reel] Forcing even dimensions: {even_w}x{even_h} for video container...")
            clip = clip.resize(newsize=(even_w, even_h))
            
        W, H = even_w, even_h
        
        # Apply premium cinematic zoom and pan effect to make the static image feel like moving footage
        def cinematic_motion(get_frame, t):
            frame = get_frame(t)
            h, w, c = frame.shape
            
            # Gentle zoom factor: from 1.0 to 1.15 over 5 seconds
            scale = 1.0 + 0.03 * t
            
            # Sub-rectangle dimensions to crop
            crop_w = int(w / scale)
            crop_h = int(h / scale)
            
            # Slow cinematic pan from left to center
            max_pan_x = int(w * 0.03)
            pan_x = int(max_pan_x * (1.0 - (t / 5.0)))
            
            x1 = max(0, (w - crop_w) // 2 - pan_x)
            y1 = max(0, (h - crop_h) // 2)
            
            # Ensure boundaries are strictly safe
            x2 = min(w, x1 + crop_w)
            y2 = min(h, y1 + crop_h)
            
            cropped = frame[y1:y2, x1:x2]
            
            # Resize cropped region back to the container dimensions using high-quality anti-aliasing
            img = Image.fromarray(cropped)
            resized_img = img.resize((w, h), Image.Resampling.LANCZOS)
            
            import numpy as np
            return np.array(resized_img)
            
        clip = clip.fl(cinematic_motion)
        clip = clip.set_duration(5)

        # Integrate high-quality background audio with a smooth fade-out for looping
        has_audio = False
        try:
            music_path = self.download_background_music()
            if music_path and os.path.exists(music_path):
                from moviepy.editor import AudioFileClip
                print("[Music] Mixing high-energy background audio track...")
                # Slice first 5 seconds of the audio and fade out the last 1.0s for a clean loop
                audio = AudioFileClip(music_path).subclip(0, 5).audio_fadeout(1.0)
                clip = clip.set_audio(audio)
                has_audio = True
                print("[Music] Background track successfully mixed into video.")
        except Exception as audio_err:
            print(f"[Music Warning] Could not integrate audio track ({audio_err}). Proceeding without sound.")

        # Set frames per second and render video file
        clip.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio=has_audio, 
            verbose=False, 
            logger=None
        )

        print(f"Reel successfully saved to {output_path}")
        return output_path

if __name__ == "__main__":
    # Test the Media module (assuming HF_API_KEY is set and valid)
    try:
        media = MayaMedia()
        # prompt = "A photorealistic candid shot of a beautiful 23-year-old half-Indian half-Italian woman in Mumbai."
        # media.generate_image(prompt, "test_image.jpg")
        # media.create_reel_from_image("test_image.jpg", "test_reel.mp4")
        print("Media module initialized.")
    except Exception as e:
        print(f"Media Module Error: {e}")
