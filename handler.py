import os
import uuid
import subprocess
import requests
import runpod
import base64

TMP_DIR = "/tmp"
os.makedirs(TMP_DIR, exist_ok=True)

def download_file(url, path):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)

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

    # command = [
    #     "python",
    #     "facefusion.py",
    #     "headless-run",
    #     "--source-paths", source_path,
    #     "--target-path", target_path,
    #     "--output-path", output_path,
    #     "--face-swapper-model", "inswapper_128"
    # ]

        command = [
        "python",
        "facefusion.py",
        "headless-run",
        "--source-paths", source_path,
        "--target-path", target_path,
        "--output-path", output_path,
        "--face-swapper-model", "inswapper_128",
        
        # --- QUICK FIX FLAGS FOR SKIN TONE & IDENTITY ---
        "--face-swapper-pixel-boost", "512",          # Forces higher resolution over the blend area
        "--face-mask-blur", "0.2"                      # Minimizes feathering so it cuts the face cleaner
    ]


    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "stderr": result.stderr,
            "stdout": result.stdout
        }

    if not os.path.exists(output_path):
        return {
            "success": False,
            "error": "FaceFusion completed but output image was not created"
        }

    # FIX: Shifted inside the handler function scope
    with open(output_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    return {
        "success": True,
        "image_base64": encoded_image
    }

# Start RunPod loop cleanly
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

