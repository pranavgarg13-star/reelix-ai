import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv


from flask import Flask, render_template, request
import uuid
from werkzeug.utils import secure_filename
import os


load_dotenv()

UPLOAD_FOLDER = "user_uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}  # images only; FFmpeg stitches these into video

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


@app.route("/create", methods=["GET", "POST"])
def create():
    myid = str(uuid.uuid4())

    if request.method == "POST":
        rec_id = str(uuid.uuid4())
        desc = request.form.get("text", "").strip()

        if not rec_id:
            return "Invalid request", 400

        folder_path = os.path.join(app.config["UPLOAD_FOLDER"], rec_id)
        os.makedirs(folder_path, exist_ok=True)

        # Save description text
        with open(os.path.join(folder_path, "desc.txt"), "w", encoding="utf-8") as f:
            f.write(desc)

        image_index = 1

        # Save uploaded images
        for key in request.files:
            file = request.files[key]

            if file and allowed_file(file.filename):
               cloudinary.uploader.upload(
        file,
        folder=f"reelix/{rec_id}",
        public_id=f"img_{image_index}",
        overwrite=True
    )
               image_index += 1

    return render_template("create.html", myid=myid, success=True)

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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static/reels", exist_ok=True)

if __name__ == "__main__":
    

    app.run(debug=False)
