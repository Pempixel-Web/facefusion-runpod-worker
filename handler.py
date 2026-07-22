import os
import uuid
import base64
import subprocess
import requests
import runpod

TMP_DIR = "/tmp"
os.makedirs(TMP_DIR, exist_ok=True)


def download_file(url, path):
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    with open(path, "wb") as f:
        f.write(response.content)


def handler(job):
    source_path = None
    target_path = None
    output_path = None

    try:
        job_input = job["input"]

        source_url = job_input.get("source_image")
        target_url = job_input.get("target_image")

        if not source_url or not target_url:
            return {
                "success": False,
                "error": "source_image and target_image are required."
            }

        source_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_source.jpg")
        target_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_target.png")
        output_path = os.path.join(TMP_DIR, f"{uuid.uuid4()}_output.png")

        download_file(source_url, source_path)
        download_file(target_url, target_path)

        command = [
            "python",
            "facefusion.py",
            "headless-run",
            "--config-path",
            "facefusion.ini",
            "--source-paths",
            source_path,
            "--target-path",
            target_path,
            "--output-path",
            output_path
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": "FaceFusion execution failed.",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command),
                "cwd": os.getcwd()
            }

        if not os.path.exists(output_path):
            return {
                "success": False,
                "error": "FaceFusion finished but output image was not created.",
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        with open(output_path, "rb") as image_file:
            image_base64 = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        return {
            "success": True,
            "image_base64": image_base64
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "FaceFusion timed out after 600 seconds."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        for file in [source_path, target_path, output_path]:
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass


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
#         f.write(response.)


# def handler(job):
#     job_input = job["input"]

#     source_url = job_inpcontentut["source_image"]
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