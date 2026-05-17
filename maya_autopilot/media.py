import os
import io
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class MayaMedia:
    def __init__(self):
        self.hf_api_key = os.getenv("HF_API_KEY")
        if not self.hf_api_key:
            raise ValueError("HF_API_KEY not found in environment variables.")

        # Using a free high-quality model from Hugging Face for image generation
        # e.g., Stable Diffusion XL
        self.api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        self.headers = {"Authorization": f"Bearer {self.hf_api_key}"}

    def generate_image(self, prompt, output_path="output.jpg"):
        """
        Calls Hugging Face Inference API to generate an image based on the prompt.
        """
        import time
        print(f"Generating image with prompt: {prompt}")
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
            response = requests.post(self.api_url, headers=self.headers, json=payload)

            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                image.save(output_path)
                print(f"Image successfully saved to {output_path}")
                return output_path
            elif response.status_code == 503:
                print(f"Model is loading/unavailable (Attempt {attempt+1}/{max_retries}). Waiting 20 seconds...")
                time.sleep(20)
            else:
                raise Exception(f"Failed to generate image: {response.status_code} - {response.text}")

        raise Exception(f"Failed to generate image after {max_retries} retries: Model failed to wake up.")

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
