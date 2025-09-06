import os
import json
import base64
from typing import Dict, Any, Optional
from PIL import Image
from io import BytesIO
from openai import OpenAI
import re
from ..config import settings

class AIService:
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def compress_image_efficiently(self, image: Image.Image, max_pixels: int = 400000, quality: int = 75) -> Optional[Image.Image]:
        """Compress image for OpenAI while maintaining quality for detection"""
        try:
            width, height = image.size
            total_pixels = width * height

            if total_pixels > max_pixels:
                scale_factor = (max_pixels / total_pixels) ** 0.5
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to RGB if needed
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    rgb_image.paste(image, mask=image.split()[-1])
                else:
                    rgb_image.paste(image)
                image = rgb_image
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            return image

        except Exception as e:
            raise ValueError(f"Image compression error: {e}")

    def image_to_base64(self, image: Image.Image) -> str:
        """Convert image to base64 with memory management"""
        try:
            compressed = self.compress_image_efficiently(image, max_pixels=300000, quality=80)
            if not compressed:
                raise ValueError("Failed to compress image")

            buffer = BytesIO()
            compressed.save(buffer, format="JPEG", quality=80, optimize=True)
            img_bytes = buffer.getvalue()
            base64_str = base64.b64encode(img_bytes).decode('utf-8')
            buffer.close()
            
            return base64_str

        except Exception as e:
            raise ValueError(f"Base64 conversion error: {e}")

    def analyze_gym_equipment(self, image_path: str, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        """Use GPT-4o to detect both asset tags and equipment in gym images"""
        try:
            # Load and process image
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            image = Image.open(image_path)
            base64_image = self.image_to_base64(image)
            
            # Check size limit (OpenAI has ~20MB limit)
            if len(base64_image) > 15 * 1024 * 1024:  # 15MB safety margin
                raise ValueError("Image too large after compression")

            prompt = """You are an expert gym equipment analyzer. Analyze this image and identify:

1. Any asset tags, labels, barcodes, or identification codes on equipment
2. All gym equipment visible with their weights/specifications
3. Equipment condition if visible

Return a JSON response with this exact structure:
{
  "asset_tags": [
    {
      "tag": "asset_tag_text",
      "confidence": 0.95,
      "location_description": "where on the equipment"
    }
  ],
  "equipment": [
    {
      "type": "dumbbell/barbell_plate/kettlebell/medicine_ball/resistance_band/cable_attachment/bench/other",
      "weight": "25 lbs" or "unknown",
      "description": "detailed description",
      "condition": "excellent/good/fair/poor/unknown",
      "suggested_asset_tag": "suggested tag if no tag visible",
      "location_in_image": "description of location in image"
    }
  ],
  "image_quality": "excellent/good/fair/poor",
  "total_items": 0,
  "recommendations": "any suggestions for better detection"
}

Be thorough but concise. If you see multiple identical items (like a rack of dumbbells), list each separately.
For asset tags, look for any text/codes that could be used for tracking - stickers, engraved text, barcodes, etc.
For equipment, be specific about weights and types."""

            # Use GPT-4o model
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )

            content = response.choices[0].message.content

            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    # Calculate confidence score based on results
                    confidence_score = self._calculate_confidence_score(result)
                    result["confidence_score"] = confidence_score
                    
                    return result
                else:
                    return {"error": "No valid JSON in response", "raw_response": content}
            except json.JSONDecodeError:
                return {"error": "Failed to parse JSON", "raw_response": content}

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
        finally:
            if 'image' in locals():
                image.close()

    def _calculate_confidence_score(self, result: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on analysis results"""
        try:
            scores = []
            
            # Asset tag confidence
            asset_tags = result.get('asset_tags', [])
            if asset_tags:
                tag_confidences = [tag.get('confidence', 0) for tag in asset_tags]
                scores.extend(tag_confidences)
            
            # Image quality score
            image_quality = result.get('image_quality', 'unknown')
            quality_scores = {
                'excellent': 1.0,
                'good': 0.8,
                'fair': 0.6,
                'poor': 0.3,
                'unknown': 0.5
            }
            scores.append(quality_scores.get(image_quality.lower(), 0.5))
            
            # Equipment detection score (based on detail level)
            equipment = result.get('equipment', [])
            if equipment:
                detail_score = 0.8 if len(equipment) > 0 else 0.3
                scores.append(detail_score)
            
            # Return average score or default
            return sum(scores) / len(scores) if scores else 0.5
            
        except Exception:
            return 0.5