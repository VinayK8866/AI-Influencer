import os
import json
import time

class BudgetGovernor:
    def __init__(self, state_file="state.json"):
        self.state_file = state_file
        # Default limits
        self.daily_limit = 2.00
        self.per_action_limit = 0.50
        
    def _load_budget_state(self):
        state = {}
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
            except Exception as e:
                print(f"[BudgetGovernor Warning] Failed to load state: {e}")
        
        budget = state.setdefault("budget", {
            "daily_spend_limit": self.daily_limit,
            "per_action_limit": self.per_action_limit,
            "today_spend": 0.0,
            "total_spend": 0.0,
            "last_reset_date": time.strftime("%Y-%m-%d")
        })
        
        # Reset daily spend if the day has changed
        today = time.strftime("%Y-%m-%d")
        if budget.get("last_reset_date") != today:
            budget["today_spend"] = 0.0
            budget["last_reset_date"] = today
            self._save_budget_state(state)
            
        return state, budget
        
    def _save_budget_state(self, state):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"[BudgetGovernor Error] Failed to save state: {e}")
            
    def check_budget(self, estimated_cost):
        """
        Validates if adding the estimated cost exceeds daily or per-action limits.
        If DRY_RUN is active, it only prints warnings.
        """
        is_dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        state, budget = self._load_budget_state()
        
        daily_limit = budget.get("daily_spend_limit", self.daily_limit)
        per_action_limit = budget.get("per_action_limit", self.per_action_limit)
        today_spend = budget.get("today_spend", 0.0)
        
        print(f"[Budget] Checking cost: ${estimated_cost:.4f}. Today: ${today_spend:.4f}/${daily_limit:.2f}")
        
        if estimated_cost > per_action_limit:
            msg = f"Action cost ${estimated_cost:.4f} exceeds per-action limit ${per_action_limit:.2f}"
            if not is_dry_run:
                raise Exception(f"[BUDGET BLOCK] {msg}")
            else:
                print(f"[BUDGET WARNING] {msg} (Proceeding in DRY_RUN)")
                
        if today_spend + estimated_cost > daily_limit:
            msg = f"Projected spend (${today_spend + estimated_cost:.4f}) exceeds daily spend limit ${daily_limit:.2f}"
            if not is_dry_run:
                raise Exception(f"[BUDGET BLOCK] {msg}")
            else:
                print(f"[BUDGET WARNING] {msg} (Proceeding in DRY_RUN)")
                
    def record_spend(self, actual_cost):
        """
        Records actual cost spent.
        """
        state, budget = self._load_budget_state()
        budget["today_spend"] = round(budget.get("today_spend", 0.0) + actual_cost, 4)
        budget["total_spend"] = round(budget.get("total_spend", 0.0) + actual_cost, 4)
        self._save_budget_state(state)
        print(f"[Budget] Spend recorded: ${actual_cost:.4f}. Daily total: ${budget['today_spend']:.4f}")


class QualityGate:
    def __init__(self, brain=None):
        self.brain = brain
        
    def verify_image(self, image_path):
        """
        Verify the image is valid and photorealistic using PIL and Gemini Vision.
        """
        print(f"[QualityGate] Verifying image asset: {image_path}")
        if not os.path.exists(image_path):
            print(f"[QualityGate Error] File not found: {image_path}")
            return False
            
        # File size check
        size_kb = os.path.getsize(image_path) / 1024
        print(f"[QualityGate] Image file size: {size_kb:.2f} KB")
        if size_kb < 10:
            print("[QualityGate Error] Image file size is too small (< 10 KB).")
            return False
            
        # PIL read check
        from PIL import Image
        try:
            with Image.open(image_path) as img:
                img.verify()
            print("[QualityGate] Image is not corrupted (PIL verify passed).")
        except Exception as e:
            print(f"[QualityGate Error] PIL verify failed: {e}")
            return False
            
        # Gemini Vision Check
        if self.brain:
            print("[QualityGate] Running Gemini Vision critique...")
            passed = self.brain.verify_image(image_path)
            if not passed:
                print("[QualityGate Error] Gemini Vision critique failed.")
                return False
            print("[QualityGate] Gemini Vision critique passed.")
        else:
            print("[QualityGate Warning] No brain provided. Skipping Gemini Vision check.")
            
        return True
        
    def verify_video(self, video_path):
        """
        Verify the video is valid using moviepy.
        """
        print(f"[QualityGate] Verifying video asset: {video_path}")
        if not os.path.exists(video_path):
            print(f"[QualityGate Error] File not found: {video_path}")
            return False
            
        # File size check
        size_kb = os.path.getsize(video_path) / 1024
        print(f"[QualityGate] Video file size: {size_kb:.2f} KB")
        if size_kb < 100:
            print("[QualityGate Error] Video file size is too small (< 100 KB).")
            return False
            
        # Moviepy metadata checks
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_path)
            duration = clip.duration
            width, height = clip.size
            clip.close()
            
            print(f"[QualityGate] Video duration: {duration:.2f}s | Resolution: {width}x{height}")
            
            if duration < 3.0:
                print(f"[QualityGate Error] Video duration too short: {duration}s (< 3.0s)")
                return False
                
            # Aspect ratio check: aspect ratio should be vertical (~9:16)
            aspect_ratio = width / height
            if not (0.5 <= aspect_ratio <= 0.65):
                print(f"[QualityGate Warning] Aspect ratio is {aspect_ratio:.2f}. Expected ~0.56 (9:16).")
                
            print("[QualityGate] Video metadata verification passed.")
            return True
        except Exception as e:
            print(f"[QualityGate Error] Video verify failed: {e}")
            return False
