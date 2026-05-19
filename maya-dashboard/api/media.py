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
            print("[FALLBACK] Automatically downgrading to Static Photo generation to prevent pipeline crash...")
            # We fallback to generating a static image using the same prompt,
            # and then convert it into a static 5-second MP4 reel so the rest of the pipeline doesn't break.
            fallback_jpg_path = output_path.replace(".mp4", ".jpg")
            self.generate_image(prompt, output_path=fallback_jpg_path)

            print("[FALLBACK] Converting fallback image to Reel format...")
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

        if last_error:
            raise last_error
        raise Exception("All Hugging Face fallback models failed to generate the image.")

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

    def create_reel_from_image(self, image_path, output_path="output.mp4"):
        """
        Creates a basic "Reel" (short video) from a static image.
        For a completely free tier without API limits, we use moviepy to make a panning/zooming
        effect on the image to simulate motion.
        """
        from moviepy.editor import ImageClip

        print(f"Converting image {image_path} to Reel {output_path}")

        # Load the image
        clip = ImageClip(image_path)

        # Make a simple 5-second video from the image
        # Note: A real implementation might add Ken Burns effect (zoom/pan) or attach audio.
        # For simplicity and robust execution without complex ffmpeg filters, we create a static 5s clip.
        clip = clip.set_duration(5)

        # Set frames per second
        clip.write_videofile(output_path, fps=24, codec="libx264", audio=False, verbose=False, logger=None)

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
