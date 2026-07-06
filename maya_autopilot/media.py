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
        self.muapi_api_key = os.getenv("MUAPI_API_KEY")

        if not self.xai_api_key and not self.muapi_api_key:
            print("Warning: Neither XAI_API_KEY nor MUAPI_API_KEY found. Media generation will fall back to legacy HF/mock mode.")
        else:
            print("[MayaMedia] Initialized with active API credentials.")

    def _get_xai_client(self):
        """Returns an initialized xAI SDK client."""
        import xai_sdk
        return xai_sdk.Client(api_key=self.xai_api_key)

    # ---------------------------------------------------------------------------
    # VIDEO GENERATION
    # ---------------------------------------------------------------------------

    def generate_video(self, prompt, output_path="output.mp4", viral_hook_text=None):
        """
        Generates a native 9:16 short-form video using the best scored available video provider.
        Falls back to: Best Image → Wan2.1 HF animation → local Ken Burns cinematic engine.
        """
        import datetime
        import time
        from governance import BudgetGovernor
        governor = BudgetGovernor()

        xai_key = self.xai_api_key
        muapi_key = self.muapi_api_key
        hf_key = os.getenv("HF_API_KEY")

        # Available video models and their performance scoring profiles
        # Score = (Quality * 0.4) + (Reliability * 0.4) - (Cost * 2.0)
        all_video_providers = [
            {"name": "xai-grok", "endpoint": "grok-imagine-video", "quality": 9.0, "reliability": 9.0, "cost": 0.40, "required_key": xai_key},
            {"name": "muapi-seedance-pro", "endpoint": "/seedance-pro-t2v", "quality": 9.0, "reliability": 8.5, "cost": 0.35, "required_key": muapi_key},
            {"name": "muapi-kling-v3", "endpoint": "/kling-v3.0-standard-text-to-video", "quality": 8.5, "reliability": 8.5, "cost": 0.25, "required_key": muapi_key},
            {"name": "muapi-runway", "endpoint": "/runway-text-to-video", "quality": 8.5, "reliability": 8.0, "cost": 0.30, "required_key": muapi_key},
            {"name": "muapi-wan2.1", "endpoint": "/wan2.1-text-to-video", "quality": 8.0, "reliability": 9.0, "cost": 0.15, "required_key": muapi_key},
            {"name": "muapi-veo3", "endpoint": "/veo3-fast-text-to-video", "quality": 8.0, "reliability": 8.0, "cost": 0.20, "required_key": muapi_key},
            {"name": "muapi-seedance-lite", "endpoint": "/seedance-lite-t2v", "quality": 7.0, "reliability": 8.5, "cost": 0.10, "required_key": muapi_key}
        ]

        # Filter available ones
        available_providers = [p for p in all_video_providers if p["required_key"]]

        scored_providers = []
        for p in available_providers:
            score = (p["quality"] * 0.4) + (p["reliability"] * 0.4) - (p["cost"] * 2.0)
            scored_providers.append((score, p))

        scored_providers.sort(key=lambda x: x[0], reverse=True)

        print("\n[Provider Selection] Scored available video providers:")
        for score, p in scored_providers:
            print(f" - {p['name']} ({p['endpoint']}): Score {score:.2f} (Quality: {p['quality']}, Reliability: {p['reliability']}, Cost: ${p['cost']})")

        generation_success = False

        for score, provider in scored_providers:
            cost = provider["cost"]
            name = provider["name"]
            endpoint = provider["endpoint"]

            # Check budget limit before calling
            try:
                governor.check_budget(cost)
            except Exception as budget_err:
                print(f"[Budget Block] Skipping {name} (${cost}): {budget_err}")
                continue

            print(f"\n[Generation] Executing {name} with endpoint {endpoint} (Cost: ${cost})...")

            try:
                if name == "xai-grok":
                    client = self._get_xai_client()
                    response = client.video.generate(
                        prompt=prompt,
                        model=endpoint,
                        aspect_ratio="9:16",
                        duration=5,
                        resolution="720p",
                        timeout=datetime.timedelta(minutes=10)
                    )
                    video_url = response.url
                    video_data = requests.get(video_url, timeout=60)
                    with open(output_path, "wb") as f:
                        f.write(video_data.content)
                else:  # Muapi
                    api_url = "https://api.muapi.ai/api/v1"
                    headers = {"x-api-key": muapi_key, "Content-Type": "application/json"}
                    payload = {"prompt": prompt, "duration": 5, "aspect_ratio": "9:16"}

                    full_endpoint = f"{api_url}{endpoint}"
                    submit_res = requests.post(full_endpoint, headers=headers, json=payload, timeout=60)
                    if submit_res.status_code not in [200, 202]:
                        raise Exception(f"Submission failed: {submit_res.status_code} - {submit_res.text}")

                    data = submit_res.json()
                    request_id = data.get("request_id")
                    if not request_id:
                        raise Exception("No request_id returned from Muapi.")

                    # Poll
                    poll_endpoint = f"{api_url}/predictions/{request_id}/result"
                    max_attempts = 60
                    completed = False
                    for attempt in range(max_attempts):
                        time.sleep(10)
                        print(f"[Muapi] Polling... (Attempt {attempt+1}/{max_attempts})")
                        poll_res = requests.get(poll_endpoint, headers=headers, timeout=30)
                        if poll_res.status_code != 200:
                            continue
                        poll_data = poll_res.json()
                        status = poll_data.get("status")
                        if status == "completed":
                            video_url = poll_data.get("output_url") or poll_data.get("video_url")
                            if not video_url:
                                raise Exception("Job completed but no video URL.")
                            video_data = requests.get(video_url, timeout=60)
                            with open(output_path, "wb") as f:
                                f.write(video_data.content)
                            completed = True
                            break
                        elif status in ["failed", "error"]:
                            raise Exception(f"Muapi job failed: {poll_data}")

                    if not completed:
                        raise Exception("Muapi job timed out.")

                print(f"[Generation] Successfully generated video using {name} and saved to {output_path}")
                governor.record_spend(cost)
                generation_success = True
                break
            except Exception as gen_err:
                print(f"[Generation Warning] {name} generation failed: {gen_err}")
                continue

        if generation_success:
            # Mix background music
            try:
                print("[Video Post-Gen] Mixing background audio track...")
                self.add_music_to_video(output_path)
            except Exception as audio_err:
                print(f"[Music Warning] Could not mix music: {audio_err}")

            # Burn viral hook overlay
            if viral_hook_text:
                try:
                    print(f"[Video Post-Gen] Burning viral hook overlay...")
                    self.overlay_text_on_video(output_path, viral_hook_text)
                except Exception as overlay_err:
                    print(f"[Overlay Warning] Could not overlay text: {overlay_err}")

            return output_path

        # ---- FALLBACK: Generate image first ----
        print("[FALLBACK] Video generation failed or blocked. Generating high-fidelity 9:16 portrait image for animation...")
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
        Generates a high-quality image using the best scored available image provider.
        Supports aspect_ratio: "1:1" (square posts) or "9:16" (portrait Reels).
        Falls back to HF Inference API if primary keys fail.
        """
        import time
        from governance import BudgetGovernor
        governor = BudgetGovernor()

        xai_key = self.xai_api_key
        muapi_key = self.muapi_api_key
        hf_key = os.getenv("HF_API_KEY")

        all_image_providers = [
            {"name": "xai-grok", "endpoint": "grok-imagine-image", "quality": 9.0, "reliability": 9.0, "cost": 0.05, "required_key": xai_key},
            {"name": "muapi-flux-dev", "endpoint": "/flux-dev", "quality": 9.0, "reliability": 9.0, "cost": 0.03, "required_key": muapi_key},
            {"name": "muapi-midjourney-v8", "endpoint": "/midjourney-v8", "quality": 9.0, "reliability": 8.5, "cost": 0.05, "required_key": muapi_key},
            {"name": "muapi-midjourney-v7", "endpoint": "/midjourney-v7", "quality": 8.0, "reliability": 8.0, "cost": 0.04, "required_key": muapi_key},
            {"name": "muapi-flux-schnell", "endpoint": "/flux-schnell", "quality": 7.5, "reliability": 9.0, "cost": 0.01, "required_key": muapi_key},
            {"name": "hf-flux-schnell", "endpoint": "black-forest-labs/FLUX.1-schnell", "quality": 7.5, "reliability": 8.5, "cost": 0.00, "required_key": hf_key},
            {"name": "hf-sd-2.1", "endpoint": "stabilityai/stable-diffusion-2-1", "quality": 6.0, "reliability": 8.0, "cost": 0.00, "required_key": hf_key}
        ]

        # Filter available ones
        available_providers = [p for p in all_image_providers if p["required_key"]]

        scored_providers = []
        for p in available_providers:
            score = (p["quality"] * 0.4) + (p["reliability"] * 0.4) - (p["cost"] * 2.0)
            scored_providers.append((score, p))

        scored_providers.sort(key=lambda x: x[0], reverse=True)

        print("\n[Provider Selection] Scored available image providers:")
        for score, p in scored_providers:
            print(f" - {p['name']} ({p['endpoint']}): Score {score:.2f} (Quality: {p['quality']}, Reliability: {p['reliability']}, Cost: ${p['cost']})")

        generation_success = False

        for score, provider in scored_providers:
            cost = provider["cost"]
            name = provider["name"]
            endpoint = provider["endpoint"]

            # Check budget limit before calling
            try:
                governor.check_budget(cost)
            except Exception as budget_err:
                print(f"[Budget Block] Skipping {name} (${cost}): {budget_err}")
                continue

            print(f"\n[Generation] Executing {name} with endpoint {endpoint} (Cost: ${cost})...")

            try:
                if name == "xai-grok":
                    client = self._get_xai_client()
                    response = client.image.sample(
                        prompt=prompt,
                        model=endpoint,
                        aspect_ratio=aspect_ratio,
                        resolution="1k"
                    )
                    img = Image.open(io.BytesIO(response.image))
                    img.save(output_path)
                elif name.startswith("muapi-"):
                    api_url = "https://api.muapi.ai/api/v1"
                    headers = {"x-api-key": muapi_key, "Content-Type": "application/json"}
                    payload = {"prompt": prompt, "num_images": 1, "width": 1024, "height": 1024}
                    if aspect_ratio == "9:16":
                        payload["width"] = 768
                        payload["height"] = 1344

                    full_endpoint = f"{api_url}{endpoint}"
                    submit_res = requests.post(full_endpoint, headers=headers, json=payload, timeout=60)
                    if submit_res.status_code not in [200, 202]:
                        raise Exception(f"Submission failed: {submit_res.status_code} - {submit_res.text}")

                    data = submit_res.json()
                    request_id = data.get("request_id")
                    if not request_id:
                        raise Exception("No request_id returned from Muapi.")

                    poll_endpoint = f"{api_url}/predictions/{request_id}/result"
                    max_attempts = 30
                    completed = False
                    for attempt in range(max_attempts):
                        time.sleep(10)
                        print(f"[Muapi] Polling... (Attempt {attempt+1}/{max_attempts})")
                        poll_res = requests.get(poll_endpoint, headers=headers, timeout=30)
                        if poll_res.status_code != 200:
                            continue
                        poll_data = poll_res.json()
                        status = poll_data.get("status")
                        if status == "completed":
                            image_url = poll_data.get("output_url") or poll_data.get("image_url")
                            if not image_url and poll_data.get("outputs"):
                                image_url = poll_data.get("outputs")[0]
                            if image_url:
                                img_res = requests.get(image_url, timeout=60)
                                with open(output_path, "wb") as f:
                                    f.write(img_res.content)
                                completed = True
                                break
                            else:
                                raise Exception("Job completed but no image URL.")
                        elif status in ["failed", "error"]:
                            raise Exception(f"Muapi image generation failed: {poll_data}")

                    if not completed:
                        raise Exception("Muapi image generation timed out.")
                else:  # HF
                    w = 768 if aspect_ratio == "9:16" else 1024
                    h = 1344 if aspect_ratio == "9:16" else 1024
                    url = f"https://router.huggingface.co/hf-inference/models/{endpoint}"

                    if "flux" in endpoint.lower():
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
                                print(f"[HF Fallback] Image saved via {endpoint}")
                                break
                            elif response.status_code == 503:
                                print(f"[HF Fallback] Model loading... waiting 20s (attempt {attempt+1}/3)")
                                time.sleep(20)
                            else:
                                print(f"[HF Fallback] {endpoint} returned {response.status_code}")
                                raise Exception(f"{endpoint}: {response.status_code}")
                        except Exception as e:
                            print(f"[HF Fallback] Error: {e}")
                            if attempt == 2:
                                raise e
                            time.sleep(5)

                print(f"[Generation] Successfully generated image using {name} and saved to {output_path}")
                governor.record_spend(cost)
                generation_success = True
                break
            except Exception as gen_err:
                print(f"[Generation Warning] {name} generation failed: {gen_err}")
                continue

        # ---- MOCK (DRY_RUN only) ----
        if not generation_success:
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
            else:
                raise Exception("Image generation failed. Add XAI_API_KEY with credits, or HF_API_KEY / MUAPI_API_KEY as fallback.")

        return output_path

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
