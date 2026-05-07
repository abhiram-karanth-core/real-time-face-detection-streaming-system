import base64
import io
import uuid
from typing import Optional, Tuple, Dict, Any

import mediapipe as mp
from PIL import Image, ImageDraw
import numpy as np


#initialise mediapipe's face detector once at module level.
#this avoids re-loading the model on every frame - it's expensive (~100ms).
#min_detection_confidence=0.5 means we only accept detections the model is
#at least 50% confident about.
_mp_face = mp.solutions.face_detection
_detector = _mp_face.FaceDetection(min_detection_confidence=0.5)


def process_frame(base64_frame: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    #decode base64 -> raw bytes -> PIL Image
    img_bytes = base64.b64decode(base64_frame)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    width, height = img.size

    #run mediapipe detection.
    #calculations cant be done on PIL image, so convert to numpy array and
    # pass to mediapipe.  
    img_np = np.array(img)
    results = _detector.process(img_np) 

    roi = None

    if results.detections:
        det = results.detections[0] #taking the first detected face only, anyways the problem statement only requires one face to be detected.
        bb = det.location_data.relative_bounding_box

        #mediapipe returns relative coordinates (0.0–1.0).
        #multiply by actual pixel dimensions to get absolute pixel coords.
        x = int(bb.xmin * width)
        y = int(bb.ymin * height)
        bw = int(bb.width * width)
        bh = int(bb.height * height)

        #basically, this is just a sanity check to avoid negative coordinates or boxes that extend beyond the image
        x  = max(0, x)
        y  = max(0, y)
        bw = min(bw, width - x)
        bh = min(bh, height - y)

        # draw the bounding box using Pillow - no OpenCV
        # ImageDraw.rectangle() takes [x0, y0, x1, y1].
        draw = ImageDraw.Draw(img)
        draw.rectangle([x, y, x + bw, y + bh], outline="red", width=3)

        roi = {
            "frame_id": str(uuid.uuid4()),
            "x": x,
            "y": y,
            "width": bw,
            "height": bh,
            # det.score is a list; [0] is the primary score.
            "confidence": float(det.score[0]) if det.score else None,
        }

    # re-encode to JPEG and base64 for the WebSocket response.
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)  # quality=85 keeps size manageable
    annotated_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return annotated_b64, roi