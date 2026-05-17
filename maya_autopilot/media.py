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
        print(f"Generating image with prompt: {prompt}")
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": "ugly, blurry, deformed, poorly drawn, AI-perfect, weird hands, extra limbs",
                "num_inference_steps": 50,
                "guidance_scale": 7.5
            }
        }

        response = requests.post(self.api_url, headers=self.headers, json=payload)

        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            image.save(output_path)
            print(f"Image successfully saved to {output_path}")
            return output_path
        else:
            raise Exception(f"Failed to generate image: {response.status_code} - {response.text}")

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
