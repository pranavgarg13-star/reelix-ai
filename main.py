import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import threading

from flask import Flask, render_template, request
import uuid
from werkzeug.utils import secure_filename
import os


load_dotenv()

UPLOAD_FOLDER = "user_uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}  # images only; FFmpeg stitches these into video

def start_worker():
    import generate_process
    generate_process.run_worker()

app = Flask(__name__)
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# ---------- UTIL ----------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")


# At top level - runs on startup
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static/reels", exist_ok=True)
worker_thread = threading.Thread(target=start_worker, daemon=True)
worker_thread.start()


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        rec_id = str(uuid.uuid4())
        desc = request.form.get("text", "").strip()

        # Write job file so worker knows to process this folder
        job_path = os.path.join(app.config["UPLOAD_FOLDER"], rec_id)
        os.makedirs(job_path, exist_ok=True)
        with open(os.path.join(job_path, "desc.txt"), "w", encoding="utf-8") as f:
            f.write(desc)

        # Upload images to Cloudinary
        image_index = 1
        for key in request.files:
            file = request.files[key]
            if file and allowed_file(file.filename):
                try:
                    cloudinary.uploader.upload(
                        file,
                        folder=f"reelix/{rec_id}",
                        public_id=f"img_{image_index}",
                        overwrite=True
                    )
                    print(f"Uploaded img_{image_index} to Cloudinary")
                    image_index += 1
                except Exception as e:
                    print(f"Cloudinary upload failed: {e}")

        return render_template("create.html", myid=rec_id, success=True)

    return render_template("create.html", myid=str(uuid.uuid4()))

@app.route("/gallery")
def gallery():
    import cloudinary.api
    try:
        result = cloudinary.api.resources(
            type="upload",
            prefix="reelix/reels/",
            resource_type="video",
            max_results=50
        )
        videos = [r["secure_url"] for r in result["resources"]]
    except Exception as e:
        print(f"Cloudinary error: {e}")
        videos = []

    return render_template("gallery.html", videos=videos)

# ---------- RUN ----------


if __name__ == "__main__":
    

    app.run(debug=False)
