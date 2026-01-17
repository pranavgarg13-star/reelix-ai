# CHATGPT CORRECTED

from flask import Flask, render_template, request
import uuid
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = "user_uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------- UTIL ----------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    myid = str(uuid.uuid1())

    if request.method == "POST":
        rec_id = request.form.get("uuid")
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
                ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"img_{image_index}.{ext}"
                image_index += 1

                file.save(os.path.join(folder_path, filename))

        return render_template("create.html", myid=myid, success=True)

    return render_template("create.html", myid=myid)


@app.route("/gallery")
def gallery():
    reels_dir = "static/reels"
    videos = []

    if os.path.exists(reels_dir):
        videos = os.listdir(reels_dir)

    return render_template("gallery.html", videos=videos)


# ---------- RUN ----------
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs("static/reels", exist_ok=True)

    app.run(debug=True)
