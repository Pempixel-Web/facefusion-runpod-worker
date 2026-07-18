import os
import uuid
import subprocess
import requests
import runpod

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

    download_file(source_url, source_path)
    download_file(target_url, target_path)

    command = [
        "python",
        "facefusion.py",
        "headless-run",
        "--source",
        source_path,
        "--target",
        target_path,
        "--output",
        output_path
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

    return {
        "success": True,
        "output_image": output_path
    }


runpod.serverless.start({"handler": handler})