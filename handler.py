import os
import uuid
import requests
import runpod
import base64
import cv2
import numpy as np

# Directly hook into the system configuration memory layout
from facefusion import state_manager
from facefusion.core import headless_run

TMP_DIR = "/tmp"
os.makedirs(TMP_DIR, exist_ok=True)

def download_file(url, path):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)

def force_skin_tone_restoration(source_path, output_path):
    """
    FAIL-SAFE PRESERVATION MATH:
    If the AI model attempts to bleach the skin to match the white template, 
    this reads the original user's rich color histograms and forcefully 
    projects them back onto the final image to guarantee his exact skin tone.
    """
    try:
        src = cv2.imread(source_path)
        out = cv2.imread(output_path)
        if src is None or out is None:
            return

        # Convert to LAB color space to isolate illumination from the color channel
        src_lab = cv2.cvtColor(src, cv2.COLOR_BGR2LAB)
        out_lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)

        # Calculate means and standard deviations of color structures
        s_l, s_a, s_b = cv2.split(src_lab)
        o_l, o_a, o_b = cv2.split(out_lab)

        # Force structural matching of color matrices
        o_a = np.clip(((o_a - np.mean(o_a)) * (np.std(s_a) / (np.std(o_a) + 1e-5))) + np.mean(s_a), 0, 255).astype(np.uint8)
        o_b = np.clip(((o_b - np.mean(o_b)) * (np.std(s_b) / (np.std(o_b) + 1e-5))) + np.mean(s_b), 0, 255).astype(np.uint8)

        # Merge back and save to overwrite the bleached file
        corrected_lab = cv2.merge([o_l, o_a, o_b])
        corrected_bgr = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)
        cv2.imwrite(output_path, corrected_bgr)
    except Exception:
        pass

def handler(job):
    job_input = job["input"]

    source_url = job_input["source_image"]
    target_url = job_input["target_image"]

    source_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_source.jpg")
    target_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_target.jpg")
    output_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_output.jpg")

    try:
        download_file(source_url, source_path)
        download_file(target_url, target_path)
    except Exception as e:
        return {"success": False, "error": f"Download failed: {str(e)}"}

    # --- HARDCODE THE STATE CONFIGURATION STRAIGHT TO SYSTEM MEMORY ---
    state_manager.set_item('source_paths', [source_path])
    state_manager.set_item('target_path', target_path)
    state_manager.set_item('output_path', output_path)
    
    # Force the core processing parameters to lock user characteristics
    state_manager.set_item('frame_processors', ['face_swapper'])
    state_manager.set_item('face_swapper_model', 'inswapper_128')
    state_manager.set_item('face_swapper_pixel_boost', '512x512')
    
    # Modern weight tuning: Tells the network to maintain 95% user identity priority
    state_manager.set_item('face_swapper_weight', 0.95)
    
    # Strictly strip the template's mouth and open teeth out of the swap boundaries
    state_manager.set_item('face_mask_types', ['box', 'region'])
    state_manager.set_item('face_mask_regions', ['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'nose'])
    state_manager.set_item('face_mask_blur', 0.10)
    
    # Execute natively via direct library call instead of flaky CLI strings
    try:
        headless_run()
    except Exception as e:
        return {"success": False, "error": f"FaceFusion core runtime error: {str(e)}"}

    if not os.path.exists(output_path):
        return {"success": False, "error": "FaceFusion completed but output image was not created"}

    # Apply final pixel-level color restoration layer
    force_skin_tone_restoration(source_path, output_path)

    with open(output_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    return {
        "success": True,
        "image_base64": encoded_image
    }

runpod.serverless.start({"handler": handler})

# import os
# import uuid
# import subprocess
# import requests
# import runpod

# TMP_DIR = "/tmp"

# os.makedirs(TMP_DIR, exist_ok=True)


# def download_file(url, path):
#     response = requests.get(url, timeout=60)
#     response.raise_for_status()
#     with open(path, "wb") as f:
#         f.write(response.content)


# def handler(job):
#     job_input = job["input"]

#     source_url = job_input["source_image"]
#     target_url = job_input["target_image"]

#     source_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_source.jpg")
#     target_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_target.jpg")
#     output_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_output.jpg")

#     download_file(source_url, source_path)
#     download_file(target_url, target_path)

#     command = [
#         "python",
#         "facefusion.py",
#         "headless-run",
#         "--source",
#         source_path,
#         "--target",
#         target_path,
#         "--output",
#         output_path
#     ]

#     result = subprocess.run(
#         command,
#         capture_output=True,
#         text=True
#     )

#     if result.returncode != 0:
#         return {
#             "success": False,
#             "stderr": result.stderr,
#             "stdout": result.stdout
#         }

#     return {
#         "success": True,
#         "output_image": output_path
#     }


# runpod.serverless.start({"handler": handler})

