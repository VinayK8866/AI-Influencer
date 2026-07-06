import os
import io
import requests
from PIL import Image
from dotenv import load_dotenv

# Load .env.local from the parent dashboard directory (works regardless of cwd)
_api_dir = os.path.dirname(os.path.abspath(__file__))
_dashboard_dir = os.path.dirname(_api_dir)
load_dotenv(os.path.join(_dashboard_dir, ".env.local"))
load_dotenv(os.path.join(_dashboard_dir, ".env"))
load_dotenv()  # Also pick up any local .env in cwd

class MayaMedia:
    def __init__(self):
        self.xai_api_key = os.getenv("XAI_API_KEY")

        if not self.xai_api_key:
            print("Warning: XAI_API_KEY not found. Image/video generation will fall back to dry-run mock mode.")
        else:
            print("[MayaMedia] xAI Grok Imagine API initialized successfully.")

    def _get_xai_client(self):
        """Returns an initialized xAI SDK client."""
        import xai_sdk
        return xai_sdk.Client(api_key=self.xai_api_key)

    # ---------------------------------------------------------------------------
    # VIDEO GENERATION
    # ---------------------------------------------------------------------------

    def generate_video(self, prompt, output_path="output.mp4", viral_hook_text=None):
        """
        Generates a native 9:16 short-form video using the xAI Grok Imagine Video API.
        Falls back to: xAI image → Wan2.1 HF animation → local Ken Burns cinematic engine.
        """
        import datetime

        print(f"\n[xAI Video] Requesting Video Generation. Prompt: {prompt[:100]}...")

        if self.xai_api_key:
            try:
                client = self._get_xai_client()
                print("[xAI Video] Submitting to grok-imagine-video (9:16, 5s)...")
                response = client.video.generate(
                    prompt=prompt,
                    model="grok-imagine-video",
                    aspect_ratio="9:16",
                    duration=5,
                    resolution="720p",
                    timeout=datetime.timedelta(minutes=10)
                )

                video_url = response.url
                print(f"[xAI Video] Generation complete! Downloading from {video_url}...")
                video_data = requests.get(video_url, timeout=60)
                with open(output_path, "wb") as f:
                    f.write(video_data.content)
                print(f"[xAI Video] Video saved to {output_path}")

                # Mix background music
                try:
                    print("[xAI Video] Mixing background audio track...")
                    self.add_music_to_video(output_path)
                except Exception as audio_err:
                    print(f"[Music Warning] Could not mix music: {audio_err}")

                # Burn viral hook overlay
                if viral_hook_text:
                    try:
                        print(f"[xAI Video] Burning viral hook overlay...")
                        self.overlay_text_on_video(output_path, viral_hook_text)
                    except Exception as overlay_err:
                        print(f"[Overlay Warning] Could not overlay text: {overlay_err}")

                return output_path

            except Exception as e:
                print(f"[xAI Video] Primary video generation failed: {e}")
                print("[xAI Video] Falling back to image-based pipeline...")

        # ---- FALLBACK: Generate image first ----
        print("[FALLBACK] Generating high-fidelity 9:16 portrait image for animation...")
        fallback_jpg_path = output_path.replace(".mp4", ".jpg")
        self.generate_image(prompt, output_path=fallback_jpg_path, aspect_ratio="9:16")

        # ---- FALLBACK Option A: HF Space Wan2.1 image-to-video animation ----
        try:
            print("[FALLBACK] [Option A] Attempting HF Space Wan2.1 image animation...")
            from gradio_client import Client, handle_file
            import shutil

            client = Client("multimodalart/wan2-1-fast")
            print("[FALLBACK] [Option A] Submitting to Wan2.1 Space (may queue up to 3min)...")

            result = client.predict(
                input_image=handle_file(fallback_jpg_path),
                prompt="cinematic video, beautiful influencer smiling, subtle head motion, slow cinematic camera pan",
                height=960,
                width=544,
                negative_prompt="Bright tones, overexposed, static, blurred details, low quality, watermark, text",
                duration_seconds=4,
                guidance_scale=5.0,
                steps=15,
                seed=42,
                randomize_seed=True,
                api_name="/generate_video"
            )

            if isinstance(result, tuple) and len(result) > 0:
                video_info = result[0]
                video_path = video_info.get("video") if isinstance(video_info, dict) else video_info
                if video_path and os.path.exists(video_path):
                    shutil.copy(video_path, output_path)
                    print(f"[FALLBACK] [Option A] Animated video saved to {output_path}!")

                    try:
                        self.add_music_to_video(output_path)
                    except Exception as audio_err:
                        print(f"[FALLBACK Music Warning] {audio_err}")

                    if viral_hook_text:
                        try:
                            self.overlay_text_on_video(output_path, viral_hook_text)
                        except Exception as overlay_err:
                            print(f"[FALLBACK Overlay Warning] {overlay_err}")

                    return output_path
            raise Exception("Invalid result structure from Hugging Face Space.")
        except Exception as hf_err:
            print(f"[FALLBACK] [Option A] HF Space failed ({hf_err}). Using local cinematic engine...")

        # ---- FALLBACK Option B: Local Ken Burns cinematic zoom ----
        print("[FALLBACK] [Option B] Rendering with local cinematic Ken Burns engine...")
        return self.create_reel_from_image(fallback_jpg_path, output_path=output_path, viral_hook_text=viral_hook_text)

    # ---------------------------------------------------------------------------
    # IMAGE GENERATION
    # ---------------------------------------------------------------------------

    def generate_image(self, prompt, output_path="output.jpg", aspect_ratio="1:1"):
        """
        Generates a high-quality image using the xAI Grok Imagine API.
        Supports aspect_ratio: "1:1" (square posts) or "9:16" (portrait Reels).
        Falls back to HF Inference API if xAI key is missing or has no credits.
        """
        import time
        print(f"[xAI Image] Generating image | Aspect Ratio: {aspect_ratio}")
        print(f"[xAI Image] Prompt: {prompt[:100]}...")

        if self.xai_api_key:
            try:
                client = self._get_xai_client()
                print("[xAI Image] Calling grok-imagine-image...")
                response = client.image.sample(
                    prompt=prompt,
                    model="grok-imagine-image",
                    aspect_ratio=aspect_ratio,
                    resolution="1k"
                )
                # response.image returns raw bytes
                img = Image.open(io.BytesIO(response.image))
                img.save(output_path)
                print(f"[xAI Image] Image saved to {output_path}")
                return output_path

            except Exception as e:
                print(f"[xAI Image] Generation failed: {e}")
                print("[xAI Image] Falling back to Hugging Face...")

        # ---- FALLBACK: Hugging Face Inference API ----
        hf_key = os.getenv("HF_API_KEY")
        if hf_key:
            fallback_models = [
                "black-forest-labs/FLUX.1-schnell",
                "stabilityai/stable-diffusion-2-1",
                "runwayml/stable-diffusion-v1-5"
            ]

            w = 768 if aspect_ratio == "9:16" else 1024
            h = 1344 if aspect_ratio == "9:16" else 1024

            last_error = None
            for model in fallback_models:
                print(f"[HF Fallback] Trying model: {model}")
                url = f"https://router.huggingface.co/hf-inference/models/{model}"

                if "flux" in model.lower():
                    payload = {"inputs": prompt, "parameters": {"width": w, "height": h}}
                else:
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "negative_prompt": "ugly, blurry, deformed, poorly drawn, AI-perfect, weird hands, extra limbs, cartoon",
                            "num_inference_steps": 50,
                            "guidance_scale": 7.5,
                            "width": w,
                            "height": h
                        }
                    }

                for attempt in range(3):
                    try:
                        response = requests.post(url, headers={"Authorization": f"Bearer {hf_key}"}, json=payload, timeout=60)
                        if response.status_code == 200:
                            image = Image.open(io.BytesIO(response.content))
                            image.save(output_path)
                            print(f"[HF Fallback] Image saved via {model}")
                            return output_path
                        elif response.status_code == 503:
                            print(f"[HF Fallback] Model loading... waiting 20s (attempt {attempt+1}/3)")
                            time.sleep(20)
                        else:
                            print(f"[HF Fallback] {model} returned {response.status_code}")
                            last_error = Exception(f"{model}: {response.status_code}")
                            break
                    except Exception as e:
                        print(f"[HF Fallback] Error: {e}")
                        last_error = e
                        time.sleep(5)

                print(f"[HF Fallback] {model} exhausted, trying next...")

        # ---- MOCK (DRY_RUN only) ----
        if os.getenv("DRY_RUN", "false").lower() == "true":
            print("\n[DRY_RUN] Creating mock test image...")
            w = 768 if aspect_ratio == "9:16" else 1024
            h = 1344 if aspect_ratio == "9:16" else 1024
            img = Image.new('RGB', (w, h), color=(33, 37, 43))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([(50, 50), (w-50, h-50)], outline=(255, 198, 10), width=4)
            draw.text(
                (100, h//2 - 100),
                f"MAYA AUTOPILOT\n[DRY_RUN ACTIVE]\nAspect: {aspect_ratio}\n\nPrompt Preview:\n{prompt[:80]}...",
                fill=(255, 255, 255)
            )
            img.save(output_path)
            print(f"[DRY_RUN] Mock image saved to {output_path}")
            return output_path

        raise Exception("Image generation failed. Add XAI_API_KEY with credits, or HF_API_KEY as fallback.")

    # ---------------------------------------------------------------------------
    # MOCK IMAGE (for testing)
    # ---------------------------------------------------------------------------

    def create_mock_image(self, output_path="output.jpg", text="Mock Asset", aspect_ratio="1:1"):
        """Generates a placeholder test image for local development."""
        from PIL import ImageDraw
        w = 768 if aspect_ratio == "9:16" else 1024
        h = 1344 if aspect_ratio == "9:16" else 1024
        print(f"[MOCK] Rendering mock image: {output_path}")
        img = Image.new('RGB', (w, h), color=(33, 37, 43))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(50, 50), (w-50, h-50)], outline=(255, 198, 10), width=4)
        draw.text((100, h//2 - 100), f"MAYA AUTOPILOT\n[MOCK]\n\n{text[:80]}", fill=(255, 255, 255))
        img.save(output_path)
        print(f"[MOCK] Mock image saved to {output_path}")
        return output_path

    # ---------------------------------------------------------------------------
    # IMAGE TEXT OVERLAY
    # ---------------------------------------------------------------------------

    def add_viral_text_to_image(self, image_path, text):
        """
        Draws a viral hook as a rounded iOS-style overlay directly onto the image.
        Scales text and font size dynamically based on image width.
        """
        from PIL import ImageDraw, ImageFont
        import textwrap

        print(f"[Visual] Adding viral text overlay to {image_path}")
        image = Image.open(image_path).convert("RGBA")
        overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        wrap_width = 24 if image.width < 1000 else 30
        wrapped_text = textwrap.fill(text, width=wrap_width)

        font_path = "Roboto-Bold.ttf"
        if not os.path.exists(font_path):
            import urllib.request
            print("[Font] Downloading Roboto-Bold...")
            try:
                urllib.request.urlretrieve(
                    "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf",
                    font_path
                )
            except Exception as e:
                print(f"[Font] Download failed: {e}")

        try:
            font_size = max(20, int(image.width * 0.045))
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()

        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image.width - text_width) / 2
        y = image.height * 0.45

        padding = int(image.width * 0.02)
        rect_coords = [(x - padding, y - padding), (x + text_width + padding, y + text_height + padding)]

        if hasattr(draw, "rounded_rectangle"):
            draw.rounded_rectangle(rect_coords, radius=15, fill=(0, 0, 0, 175))
        else:
            draw.rectangle(rect_coords, fill=(0, 0, 0, 175))

        draw.multiline_text((x, y), wrapped_text, font=font, fill=(255, 255, 255), align="center")

        out = Image.alpha_composite(image, overlay).convert("RGB")
        out.save(image_path)
        print("[Visual] Viral hook overlay applied successfully.")
        return image_path

    # ---------------------------------------------------------------------------
    # VIDEO TEXT OVERLAY  (PIL + MoviePy composite — no ImageMagick required)
    # ---------------------------------------------------------------------------

    def overlay_text_on_video(self, video_path, text, output_path=None):
        """
        Composites a rounded semi-transparent text hook onto a video file.
        Uses PIL to draw the overlay PNG and MoviePy for compositing.
        No ImageMagick dependency.
        """
        if not text:
            return video_path

        if not output_path:
            output_path = video_path

        print(f"[Video Overlay] Burning viral hook: '{text}'")

        from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
        from PIL import ImageDraw, ImageFont
        import textwrap

        video = VideoFileClip(video_path)
        W, H = video.size

        overlay = Image.new("RGBA", (W, H), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        wrap_width = 24 if W < 1000 else 30
        wrapped_text = textwrap.fill(text, width=wrap_width)

        font_path = "Roboto-Bold.ttf"
        if not os.path.exists(font_path):
            import urllib.request
            try:
                urllib.request.urlretrieve(
                    "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf",
                    font_path
                )
            except Exception as e:
                print(f"[Font] Download failed: {e}")

        try:
            font_size = max(20, int(W * 0.045))
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()

        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (W - text_width) / 2
        y = H * 0.45
        padding = int(W * 0.02)
        rect_coords = [(x - padding, y - padding), (x + text_width + padding, y + text_height + padding)]

        if hasattr(draw, "rounded_rectangle"):
            draw.rounded_rectangle(rect_coords, radius=15, fill=(0, 0, 0, 175))
        else:
            draw.rectangle(rect_coords, fill=(0, 0, 0, 175))

        draw.multiline_text((x, y), wrapped_text, font=font, fill=(255, 255, 255), align="center")

        temp_overlay_path = "temp_overlay.png"
        overlay.save(temp_overlay_path)

        text_clip = (ImageClip(temp_overlay_path)
                     .set_duration(video.duration)
                     .set_position("center"))

        final_video = CompositeVideoClip([video, text_clip])
        if video.audio:
            final_video = final_video.set_audio(video.audio)

        temp_output_path = "temp_burn_output.mp4"
        final_video.write_videofile(
            temp_output_path,
            fps=video.fps or 24,
            codec="libx264",
            audio=bool(video.audio),
            verbose=False,
            logger=None
        )

        video.close()
        text_clip.close()
        final_video.close()

        if os.path.exists(temp_overlay_path):
            os.remove(temp_overlay_path)

        if os.path.exists(output_path) and output_path == video_path:
            os.remove(output_path)
        import shutil
        shutil.move(temp_output_path, output_path)

        print(f"[Video Overlay] Text overlay burned onto {output_path}")
        return output_path

    # ---------------------------------------------------------------------------
    # BACKGROUND MUSIC MIXING
    # ---------------------------------------------------------------------------

    def add_music_to_video(self, video_path, output_path=None):
        """
        Downloads a copyright-safe track and mixes it into a video file.
        Trims the audio to match the exact video duration with a clean fade-out.
        """
        if not output_path:
            output_path = video_path

        music_path = self.download_background_music()
        if not music_path or not os.path.exists(music_path):
            print("[Music Warning] No music track available. Skipping audio mixing.")
            return video_path

        from moviepy.editor import VideoFileClip, AudioFileClip

        print(f"[Music] Mixing '{music_path}' into '{video_path}'...")
        video = VideoFileClip(video_path)
        duration = video.duration

        audio = AudioFileClip(music_path).subclip(0, duration).audio_fadeout(1.0)
        video = video.set_audio(audio)

        temp_output = "temp_music_output.mp4"
        video.write_videofile(temp_output, fps=video.fps or 24, codec="libx264", audio=True, verbose=False, logger=None)
        video.close()
        audio.close()

        if os.path.exists(output_path) and output_path == video_path:
            os.remove(output_path)
        import shutil
        shutil.move(temp_output, output_path)
        print(f"[Music] Audio track mixed into {output_path}")
        return output_path

    def download_background_music(self, vibe="random"):
        """
        Downloads a copyright-safe background music track.
        Tries Jamendo CC API first, then SoundHelix fallbacks.
        """
        import urllib.request
        import random
        import json

        music_dir = "assets"
        os.makedirs(music_dir, exist_ok=True)

        # 1. Jamendo CC API
        try:
            api_url = "https://api.jamendo.com/v3.0/tracks/?client_id=56d30c95&format=json&limit=30&tags=electronic,house,lounge,chill&audioformat=mp32"
            print("[Music] Querying Jamendo for copyright-safe tracks...")
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                api_data = json.loads(response.read().decode('utf-8'))
                results = api_data.get("results", [])
                if results:
                    track = random.choice(results)
                    audio_url = track.get("audio")
                    track_id = track.get("id")
                    if audio_url:
                        music_path = os.path.join(music_dir, f"jamendo_{track_id}.mp3")
                        if not os.path.exists(music_path):
                            print(f"[Music] Downloading '{track.get('name')}' from Jamendo...")
                            down_req = urllib.request.Request(audio_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(down_req, timeout=12) as down_res, open(music_path, 'wb') as f:
                                f.write(down_res.read())
                        return music_path
        except Exception as api_err:
            print(f"[Music] Jamendo API failed ({api_err}). Using SoundHelix fallback...")

        # 2. SoundHelix curated fallback
        playlist = [f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{i}.mp3" for i in range(1, 17)]
        selected = random.choice(playlist)
        song_num = selected.split("-")[-1].replace(".mp3", "")
        music_path = os.path.join(music_dir, f"bg_music_fallback_{song_num}.mp3")

        if not os.path.exists(music_path):
            print(f"[Music] Downloading SoundHelix track {song_num}...")
            try:
                req = urllib.request.Request(selected, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response, open(music_path, 'wb') as f:
                    f.write(response.read())
                print(f"[Music] Track {song_num} cached successfully.")
            except Exception as e:
                print(f"[Music] Download failed: {e}")
                existing = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.endswith(".mp3")]
                if existing:
                    return random.choice(existing)
                return None
        return music_path

    # ---------------------------------------------------------------------------
    # LOCAL CINEMATIC KEN BURNS FALLBACK
    # ---------------------------------------------------------------------------

    def create_reel_from_image(self, image_path, output_path="output.mp4", viral_hook_text=None):
        """
        Renders a cinematic Ken Burns pan+zoom Reel from a static image.
        Used as the final fallback when all video generation APIs are unavailable.
        Mixes background audio and burns in the viral hook text overlay.
        """
        # Patch PIL.Image.ANTIALIAS for modern PIL compatibility inside moviepy
        try:
            import PIL.Image
            if not hasattr(PIL.Image, 'ANTIALIAS'):
                PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
        except Exception:
            pass

        if viral_hook_text:
            print(f"[Ken Burns] Overlaying viral hook before animation: '{viral_hook_text}'")
            self.add_viral_text_to_image(image_path, text=viral_hook_text)

        from moviepy.editor import ImageClip

        print(f"[Ken Burns] Rendering cinematic video from {image_path}...")

        clip = ImageClip(image_path)

        # Enforce even dimensions (FFmpeg H.264 requirement)
        W, H = clip.size
        even_w = W - (W % 2)
        even_h = H - (H % 2)
        if even_w != W or even_h != H:
            clip = clip.resize(newsize=(even_w, even_h))
        W, H = even_w, even_h

        def cinematic_motion(get_frame, t):
            frame = get_frame(t)
            h, w, c = frame.shape

            # Gentle zoom: 1.0 → 1.15 over 5 seconds
            scale = 1.0 + 0.03 * t

            crop_w = int(w / scale)
            crop_h = int(h / scale)

            # Slow left-to-center pan
            max_pan_x = int(w * 0.03)
            pan_x = int(max_pan_x * (1.0 - (t / 5.0)))

            x1 = max(0, (w - crop_w) // 2 - pan_x)
            y1 = max(0, (h - crop_h) // 2)
            x2 = min(w, x1 + crop_w)
            y2 = min(h, y1 + crop_h)

            cropped = frame[y1:y2, x1:x2]
            img = Image.fromarray(cropped)
            resized = img.resize((w, h), Image.Resampling.LANCZOS)

            import numpy as np
            return np.array(resized)

        clip = clip.fl(cinematic_motion).set_duration(5)

        # Mix background music
        has_audio = False
        try:
            music_path = self.download_background_music()
            if music_path and os.path.exists(music_path):
                from moviepy.editor import AudioFileClip
                print("[Ken Burns] Mixing background audio...")
                audio = AudioFileClip(music_path).subclip(0, 5).audio_fadeout(1.0)
                clip = clip.set_audio(audio)
                has_audio = True
        except Exception as audio_err:
            print(f"[Ken Burns] Audio mixing failed ({audio_err}). Proceeding silent.")

        clip.write_videofile(output_path, fps=24, codec="libx264", audio=has_audio, verbose=False, logger=None)
        print(f"[Ken Burns] Cinematic Reel saved to {output_path}")
        return output_path


if __name__ == "__main__":
    try:
        media = MayaMedia()
        print("MayaMedia module initialized successfully.")
    except Exception as e:
        print(f"MayaMedia Error: {e}")
