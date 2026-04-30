from flask import Flask, jsonify, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database.supabase_client import supabase
from flask_mail import Mail, Message
from forms import AdminLoginForm, OrganizerLoginForm, OrganizerRegisterForm, RegisterEventForm, EventForm, ContactForm, StudentLoginForm, StudentRegisterForm
from dotenv import load_dotenv
from datetime import datetime
import uuid, os
import os
from werkzeug.utils import secure_filename
import random
import string
os.makedirs("static/proofs",exist_ok=True)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
#------------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'eventaggregatora@gmail.com'
app.config['MAIL_PASSWORD'] = 'ormt quos yzad hbyp'
app.config['MAIL_DEFAULT_SENDER'] = 'eventaggregatora@gmail.com'
mail = Mail(app)
def send_email(to, subject, body):
    msg = Message(subject, recipients=[to])
    msg.body = body
    mail.send(msg)
#-------------------------
def generate_secret():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORG-{code}"
#============================
@app.route("/signup_router", methods=["POST"])
def signup_router():
    role = request.form.get("signup_role")

    if role == "student":
        return redirect(url_for("register_student"))
    elif role == "organizer":
        return redirect(url_for("register_organizer"))
    else:
        flash("Invalid signup type", "danger")
        return redirect(url_for("login"))
#------------------------------
@app.route("/event/<event_id>/chat")
@login_required
def get_chat(event_id):
    res = supabase.table("event_chat").select("*").eq("event_id", event_id).order("timestamp").execute()
    return jsonify(res.data)
#------------------------------------
@app.route("/event/<event_id>/chat/send", methods=["POST"])
@login_required
def send_chat(event_id):
    message = request.json.get("message")

    data = {
        "event_id": event_id,
        "user_id": current_user.id,
        "message": message,
       "full_name": current_user.full_name,
       "role": current_user.role
    }

    supabase.table("event_chat").insert(data).execute()
    return jsonify({"status": "success"})

#-------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        
        if role == "student":
            return redirect(url_for("login_student"))
        elif role == "organizer":
            return redirect(url_for("login_organizer"))
        elif role == "admin":
            return redirect(url_for("login_admin"))
        else:
            flash("Please select a valid option.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")
#------------------------------------
@app.route("/search")
def search_events():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    # If both empty → prevent empty search
    if not q and not category:
        flash("Please enter something to search or choose a category.", "warning")
        return redirect(url_for("index"))

    query_builder = supabase.table("events").select("*")

    # Apply text search only if q is given
    if q:
        query_builder = query_builder.or_(
            f"title.ilike.%{q}%,"
            f"description.ilike.%{q}%,"
            f"venue.ilike.%{q}%,"
            f"college_name.ilike.%{q}%,"
            f"category.ilike.%{q}%"
        )

    # Apply category filter ONLY if category selected
    if category:
        query_builder = query_builder.eq("event_type", category)

    # Execute final query
    res = query_builder.execute()
    events = res.data if res.data else []

    if not events:
        flash("No events found matching your search.", "info")

    return render_template(
        "search_results.html",
        events=events,
        query=q,
        category=category
    )
#------------------------------
@app.route("/admin/delete_user/<id>", methods=["POST"])
def delete_user(id):
    supabase.table("users").delete().eq("id", id).execute()
    flash("User deleted successfully!", "success")
    return redirect(url_for("all_users"))
#-----------------------------------
@app.route("/admin/users")
def all_users():
    res = supabase.table("users").select("*").execute()
    users = res.data if res.data else []

    return render_template("all_users.html", users=users)
#------------------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")


#-----------------------------------
@app.route("/admin/approve/<id>")
def approve_organizer(id):
    code = generate_secret()

    supabase.table("users").update({
        "verified": True,
        "secret_code": code
    }).eq("id", id).execute()

    email_body = f"""
    Hi {supabase.table("users").select("full_name").eq("id", id).execute().data[0]['full_name']},
    Your organizer account has been approved!

    Your Security Code is: {code}

    Please use this code to log in as an organizer.
    Regards,
    Event Aggregator Team.
    """
    send_email(
        to=supabase.table("users").select("email").eq("id", id).execute().data[0]['email'],
        subject="Organizer Account Approved", body=email_body)


    flash("Organizer approved and email sent!","success")
    return redirect(url_for("pending_organizers"))
#-----------------------------------------
@app.route("/admin/reject/<id>")
def reject_organizer(id):
    supabase.table("users").delete().eq("id", id).execute()
    email_body = f"""
    Hi {supabase.table("users").select("full_name").eq("id", id).execute().data[0]['full_name']},
    We regret to inform you that your organizer registration has been rejected.

    Regards,
    Event Aggregator Team.
    """
    send_email(
        to=supabase.table("users").select("email").eq("id", id).execute().data[0]['email'],
        subject="Organizer Registration Rejected", body=email_body)
    supabase.table("users").delete().eq("id", id).execute()
    
    flash("Organizer rejected & email sent!", "danger")
    return redirect(url_for("pending_organizers"))
# === Secret codes
ORGANIZER_SECRET = "ORG2025"
ADMIN_SECRET = "ADMIN2025"
# Folder where uploaded files will be saved
app.config['UPLOAD_FOLDER'] = 'static/uploads' # type: ignore
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # type: ignore
# Only allow safe image formats
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
load_dotenv()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# ---------------- USER CLASS ----------------
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, password=None, role=None, verified=False,
                 name=None, full_name=None, college_name=None,
                 roll_number=None, club_name=None):
        self.id = id
        self.email = email
        self.password = password  # can be None for admin/login_user case
        self.role = role
        self.verified = verified
        self.name = name or full_name
        self.full_name = full_name or name
        self.college_name = college_name
        self.roll_number = roll_number
        self.club_name = club_name
    def is_organizer(self):
        return self.role == "organizer"
    def is_student(self):
        return self.role == "student"
    def is_admin(self):
        return self.role == "admin" or self.email == "admin@eventaggregrator.com"

@login_manager.user_loader
def load_user(user_id):
    # Prevent invalid admin UUIDs
    if user_id in ["admin", "admin-0001"]:
        return User(
            id="admin",
            email="admin@eventaggregrator.com",
            role="admin",
            verified=True
        )

    # Normal users
    try:
        data = supabase.table("users").select("*").eq("id", user_id).execute()
    except Exception as e:
        print("Error loading user:", e)
        return None

    if data.data:
        u = data.data[0]
        return User(
            id=u.get("id"),
            email=u.get("email"),
            password=u.get("password"),
            role=u.get("role"),
            verified=u.get("verified", False),
            full_name=u.get("full_name"),
            college_name=u.get("college_name"),
            roll_number=u.get("roll_number"),
            club_name=u.get("club_name")
        )
    return None


# ---------------- ROUTES ----------------
@app.route("/")
def index():
    events = supabase.table("events").select("*").order("created_at", desc=True).limit(6).execute().data
    return render_template("index.html", events=events)

#------
@app.route("/profile")
@login_required
def profile():
    # Default structure so nothing breaks even if DB fetch fails
    user_info = {
        "full_name": getattr(current_user, "full_name", "Admin User"),
        "email": current_user.email,
        "role": current_user.role,
        "college_name": getattr(current_user, "college_name", ""),
        "department": getattr(current_user, "department", ""),
        "roll_number": getattr(current_user, "roll_number", ""),
        "club_name": getattr(current_user, "club_name", ""),
        "verified": getattr(current_user, "verified", False),
    }

    # 👇 Skip DB fetch for admin (avoid UUID error)
    if current_user.role != "admin":
        try:
            res = supabase.table("users").select("*").eq("id", current_user.id).execute()
            if res.data:
                user_info.update(res.data[0])
        except Exception as e:
            print("Profile fetch error:", e)

    return render_template("profile.html", user=user_info)
# ---------- LOGOUT ----------
@app.route("/logout")
@login_required
def logout():
    from flask_login import logout_user
    logout_user()
    flash("You have been logged out successfully!", "info")
    return redirect(url_for("login"))
# ---------- DASHBOARD ----------
@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin" or current_user.email == "admin@eventaggregrator.com":
        return redirect(url_for("admin_dashboard"))

    if current_user.role == "organizer":
        events = supabase.table("events").select("*").eq("organizer_id", current_user.id).execute().data
        return render_template("dashboard.html", events=events, registered_events=None)

    if current_user.role == "student":
        regs = supabase.table("registrations").select("event_id").eq("student_id", current_user.id).execute().data
        registered_events = []
        if regs:
            ids = [r["event_id"] for r in regs]
            registered_events = supabase.table("events").select("*").in_("id", ids).execute().data
        return render_template("dashboard.html", events=None, registered_events=registered_events)

    flash("Unknown user role!", "danger")
    return redirect(url_for("login"))
#------------create
@app.route("/organizer/create-event", methods=["GET", "POST"])
@login_required
def create_event():
    if current_user.role != "organizer":
        flash("Only organizers can create events.", "danger")
        return redirect(url_for("dashboard"))

    form = EventForm()
    if form.validate_on_submit():
        image_url = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            form.image.data.save(filepath)
            image_url = f"/static/uploads/{filename}"
        notice_letter = None
        if form.notice_letter.data:
             nl_filename = secure_filename(form.notice_letter.data.filename)
             nl_filepath = os.path.join("static/letters", nl_filename)
             form.notice_letter.data.save(nl_filepath)
             notice_letter = f"/static/letters/{nl_filename}"

        

        supabase.table("events").insert({
            "title": form.title.data,
            "description": form.description.data,
            "college_name": form.college_name.data,
            "organizer_id": current_user.id,
            "event_type": form.event_type.data,
            "mode": form.mode.data,
            "date": form.date.data.isoformat(),
            "time": str(form.time.data),
            "venue": form.venue.data,
            "registration_fee": float(form.registration_fee.data or 0),
            "image_url": image_url,
           "notice_letter": notice_letter

            

        }).execute()

        flash("Event created successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("create_event.html", form=form)


# ---------- EDIT EVENT ----------
@app.route("/edit-event/<event_id>", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    if not current_user.is_organizer():
        flash("Only organizers can edit events.", "danger")
        return redirect(url_for("dashboard"))

    res = supabase.table("events").select("*").eq("id", event_id).execute()
    if not res.data:
        flash("Event not found.", "warning")
        return redirect(url_for("dashboard"))

    event = res.data[0]

    if event["organizer_id"] != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("dashboard"))

    # -------------------------

    # -------------------------
    from datetime import datetime, date, time as time_cls

    # Fix date
    if isinstance(event.get("date"), str):
        try:
            event["date"] = datetime.fromisoformat(event["date"]).date()
        except:
            event["date"] = date.today()

    # Fix time
    if isinstance(event.get("time"), str):
        try:
            event["time"] = datetime.strptime(event["time"], "%H:%M:%S").time()
        except:
            event["time"] = None

    # Fix registration_fee
    try:
        event["registration_fee"] = float(event.get("registration_fee") or 0)
    except:
        event["registration_fee"] = 0.0

    # Fix seats
    try:
        event["seats"] = int(event.get("seats") or 0)
    except:
        event["seats"] = 0

       # Pre-fill form
    # -------------------------
    form = EventForm(data=event)

    if form.validate_on_submit():

        update_data = {
            "title": form.title.data,
            "description": form.description.data,
            "event_type": form.event_type.data,
            "college_name": form.college_name.data,
            "venue": form.venue.data,
            "seats": int(form.seats.data or 0),
            "registration_fee": float(form.registration_fee.data or 0),
            "date": form.date.data.isoformat() if form.date.data else None,
            "time": str(form.time.data) if form.time.data else None,
            
        }

        # If image uploaded
        if form.image.data:
            img = form.image.data
            filename = secure_filename(img.filename)
            img.save(os.path.join("static/uploads", filename))
            update_data["image"] = filename
        if form.notice_letter.data:
            nl = form.notice_letter.data
            filename = secure_filename(nl.filename)
            nl.save(os.path.join("static/letters", filename))
            update_data["notice_letter"] = f"/static/letters/{filename}"


        supabase.table("events").update(update_data).eq("id", event_id).execute()
        flash("Event updated successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_event.html", form=form, event=event)

# ------------------ STUDENT REGISTER ------------------
@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    form = StudentRegisterForm()

    if form.validate_on_submit():
        full_name = form.full_name.data
        email = form.email.data
        password = form.password.data
        college_name = form.college_name.data
        department = form.department.data

        # CHECK IF USER EXISTS
        exists = supabase.table("users").select("*").eq("email", email).execute()
        if exists.data:
            flash("Email already registered!", "danger")
            return redirect(url_for("register_student"))

        # HASH THE PASSWORD
        hashed_password = generate_password_hash(password)

        # INSERT INTO SUPABASE
        res = supabase.table("users").insert({
            "full_name": full_name,
            "email": email,
            "password": hashed_password,  # VERY IMPORTANT
            "role": "student",
            "college_name": college_name,
            "department": department,
            "verified": True
        }).execute()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("login_student"))

    return render_template("student_signup.html", form=form)
# ------------------ ORGANIZER REGISTER ------------------
@app.route("/register/organizer", methods=["GET", "POST"])
def register_organizer():
    form = OrganizerRegisterForm()

    if form.validate_on_submit():
        proof_file = form.proof.data
        proof_filename = None

        if proof_file:
            filename = secure_filename(proof_file.filename)
            proof_filename = filename
            proof_path = os.path.join("static", "proofs", filename)
            proof_file.save(proof_path)

        # Save to Supabase
        supabase.table("users").insert({
            "full_name": form.full_name.data,
            "email": form.email.data,
            "college_name": form.college_name.data,
            "department": form.department.data,
            "club_name": form.club_name.data,
            "role": "organizer",
            "verified": False,
            "password": generate_password_hash(form.password.data),
            "proof_file": proof_filename
        }).execute()

        flash("Organizer registration submitted!", "success")
        return redirect(url_for("login_organizer"))

    return render_template("organizer_signup.html", form=form)

@app.route("/login/student", methods=["GET", "POST"])
def login_student():
    form = StudentLoginForm()

    if request.method == "POST":
        print("DEBUG FORM:", form.email.data, form.password.data)

    if form.validate_on_submit():
        email = form.email.data.strip()
        password = form.password.data

        res = supabase.table("users").select("*").eq("email", email).eq("role", "student").execute()
        print("DEBUG RESULT:", res)

        # User not found
        if not res.data:
            flash("Account not found!", "danger")
            return redirect(url_for("login_student"))

        user = res.data[0]

        # Password check
        print("STORED HASH:", user["password"])
        print("ENTERED:", password)

        if not check_password_hash(user["password"], password):
            flash("Incorrect password!", "danger")
            return redirect(url_for("login_student"))

        # Login user
        student = User(
            id=user["id"],
            full_name=user["full_name"],
            email=user["email"],
            role=user["role"],
            verified=user["verified"]
        )

        login_user(student)
        flash("Welcome student!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login_student.html", form=form)
#---------------------------
@app.route("/login/organizer", methods=["GET", "POST"])
def login_organizer():
    form = OrganizerLoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        secret = form.secret_code.data

        user_res = supabase.table("users").select("*").eq("email", email).eq("role", "organizer").execute()
        if not user_res.data:
            flash("Organizer not found!", "danger")
            return redirect(url_for("login_organizer"))

        u = user_res.data[0]

        if not check_password_hash(u["password"], password):
            flash("Incorrect password!", "danger")
            return redirect(url_for("login_organizer"))

        if u["verified"] is not True:
            flash("Admin approval pending.", "warning")
            return redirect(url_for("login_organizer"))

        if u["secret_code"] != secret:
            flash("Invalid Secret Code!", "danger")
            return redirect(url_for("login_organizer"))

        # Allow login
        user_obj = User(
            id=u["id"],
            full_name=u["full_name"],
            email=u["email"],
            role=u["role"],
            verified=u["verified"]
        )

        login_user(user_obj)
        flash("Welcome Organizer!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login_organizer.html", form=form)
#-----------Admin login
@app.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        secret_code = request.form.get("secret_code")

        admin_secret = "ADMIN2025"   # your secret code

        # pull from users table
        res = supabase.table("users").select("*").eq("email", email).execute()
        if not res.data:
            flash("Admin account not found.", "danger")
            return redirect(url_for("login_admin"))

        user = res.data[0]

        if user["role"] != "admin":
            flash("This account is not an admin.", "danger")
            return redirect(url_for("login_admin"))

        if not check_password_hash(user["password"], password):
            flash("Incorrect password.", "danger")
            return redirect(url_for("login_admin"))

        if secret_code != admin_secret:
            flash("Invalid Secret Code", "danger")
            return redirect(url_for("login_admin"))

        user_obj = User(
            id=user["id"],
            full_name=user["full_name"],
            email=user["email"],
            role=user["role"],
            verified=True
        )

        login_user(user_obj)
        flash("Welcome Admin!", "success")
        return redirect(url_for("pending_organizers"))

    return render_template("login_admin.html")
# ---------- DELETE EVENT ----------
@app.route("/delete_event/<event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
    if current_user.role != "organizer":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    event = supabase.table("events").select("*").eq("id", event_id).execute()
    if not event.data:
        flash("Event not found.", "warning")
        return redirect(url_for("dashboard"))

    event_data = event.data[0]
    if event_data["organizer_id"] != current_user.id:
        flash("You can delete only your own events.", "danger")
        return redirect(url_for("dashboard"))

    supabase.table("events").delete().eq("id", event_id).execute()
    flash("Event deleted successfully!", "success")
    return redirect(url_for("dashboard"))

# ---------- EVENT DETAIL ----------
@app.route("/event/<string:event_id>", methods=["GET", "POST"])
@login_required
def event_detail(event_id):
    # Fetch the event from Supabase
    event_data = supabase.table("events").select("*").eq("id", event_id).execute()
    if not event_data.data:
        flash("Event not found!", "danger")
        return redirect(url_for("dashboard"))

    event = event_data.data[0]

    # Check if the user already registered
    registration_check = (
        supabase.table("registrations")
        .select("*")
        .eq("event_id", event_id)
        .eq("student_id", current_user.id)
        .execute()
    )

    already_registered = len(registration_check.data) > 0

    # Handle registration
    if request.method == "POST":
        if already_registered:
            # Unregister
            supabase.table("registrations").delete().eq("event_id", event_id).eq(
                "student_id", current_user.id
            ).execute()
            flash("You have unregistered from this event.", "info")
        else:
            # Register
            supabase.table("registrations").insert(
                {"event_id": event_id, "student_id": current_user.id}
            ).execute()
            flash("You have successfully registered for this event!", "success")

        # Redirect to reload the page and show the correct button
        return redirect(url_for("event_detail", event_id=event_id))

    return render_template("event_detail.html", event=event, already_registered=already_registered)

# ---------- unREGISTER EVENT ----------
@app.route("/event/<event_id>/unregister", methods=["POST"])
@login_required
def unregister_event(event_id):
    if current_user.role != "student":
        flash("Only students can unregister from events.", "danger")
        return redirect(url_for("event_detail", event_id=event_id))

    res = supabase.table("registrations").delete().eq("event_id", event_id).eq("student_id", current_user.id).execute()

    if res.data:
        flash("You have successfully unregistered from the event.", "success")
    else:
        flash("You were not registered for this event.", "warning")

    return redirect(url_for("event_detail", event_id=event_id))
#____________________________
@app.route("/admin/verify/<user_id>", methods=["POST"])
@login_required
def verify_organizer(user_id):
    if current_user.email != "admin@eventaggregrator.com":
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))
    supabase.table("users").update({"verified": True}).eq("id", user_id).execute()
    flash("Organizer verified successfully!", "success")
    return redirect(url_for("pending_organizers"))
# ---------- VIEW EVENTS ----------
@app.route("/events")
def events_view():
    q = request.args.get("q", "")
    if q:
        res = supabase.table("events").select("*").ilike("title", f"%{q}%").execute()
    else:
        res = supabase.table("events").select("*").order("date", desc=False).execute()
    return render_template("discover.html", events=res.data, q=q)
#-----approve_organizers----------
@app.route("/admin/pending-organizers")
@login_required
def pending_organizers():
    # ✅ Only admins allowed
    if not (current_user.role == "admin" or current_user.email == "admin@eventaggregrator.com"):
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))

    # Pending organizers
    pending_res = supabase.table("users").select("*").eq("role", "organizer").eq("verified", False).execute()
    approved_res = supabase.table("users").select("*").eq("role", "organizer").eq("verified", True).execute()
    pending=pending_res.data or []
    approved=approved_res.data or[]
    return render_template("pending_organizers.html", pending=pending, approved=approved)
#------------------------
@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    avatars = ["avatar1.png","avatar2.png","avatar3.png","avatar4.png","avatar5.png"]

    if request.method == "POST":
        # read form data
        full_name = request.form.get("full_name", "").strip()
        college_name = request.form.get("college_name", "").strip()
        department = request.form.get("department", "").strip()
        club_name = request.form.get("club_name", "").strip() if current_user.role == "organizer" else None
        avatar = request.form.get("avatar")  # may be None if nothing selected

        # ensure avatar is one of allowed values (prevent malicious input)
        if avatar and avatar not in avatars:
            avatar = None

        # Build update_data only with provided values (avoid overwriting with empty strings)
        update_data = {}
        if full_name: update_data["full_name"] = full_name
        if college_name: update_data["college_name"] = college_name
        if department: update_data["department"] = department
        if club_name is not None: update_data["club_name"] = club_name
        if avatar is not None: update_data["avatar"] = avatar

        if not update_data:
            flash("No changes detected.", "info")
            return redirect(url_for("edit_profile"))

        # perform update
        res = supabase.table("users").update(update_data).eq("id", current_user.id).execute()

       
        if getattr(res, "error", None):
            flash("Failed to update profile: " + str(res.error), "danger")
            return redirect(url_for("edit_profile"))

        # fetch fresh user row to ensure DB updated (and to update local current_user)
        fetch = supabase.table("users").select("*").eq("id", current_user.id).single().execute()
        if getattr(fetch, "error", None) or not getattr(fetch, "data", None):
            # still success but we couldn't fetch updated row — just notify
            # try to at least update current_user attributes from update_data so UI reflects change
            for k, v in update_data.items():
                try:
                    setattr(current_user, k, v)
                except Exception:
                    pass
            flash("Profile updated (couldn't re-fetch user).", "warning")
            return redirect(url_for("profile"))

        # fetch.data should be a dict with the latest values
        new_user = fetch.data if hasattr(fetch, "data") else fetch.get("data")

        # update attributes on current_user for immediate reflection in templates
        for k, v in new_user.items():
            try:
                setattr(current_user, k, v)
            except Exception:
                # if current_user is not assignable for some keys, ignore
                pass

        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    # GET -> render
    return render_template("edit_profile.html",
                           user=current_user,
                           avatars=avatars)

#---------------------------------------------------
@app.route("/event/<event_id>/register", methods=["GET", "POST"])
@login_required
def event_register(event_id):

    # Check event exists
    event_res = supabase.table("events").select("*").eq("id", event_id).execute()
    if not event_res.data:
        flash("Event not found!", "danger")
        return redirect(url_for("dashboard"))

    # GET → show the form
    if request.method == "GET":
        return render_template("event_register.html", event_id=event_id)

    # POST → form submitted
    full_name = request.form.get("full_name")
    email = request.form.get("email")
    dept = request.form.get("department")
    year = request.form.get("year")
    phone = request.form.get("phone")

    # Check if already registered
    existing = supabase.table("registrations").select("*").match({
        "event_id": event_id,
        "student_id": current_user.id
    }).execute()

    if existing.data:
        flash("You already registered for this event.", "info")
        return redirect(url_for("event_detail", event_id=event_id))

    # Insert into registrations table
    supabase.table("registrations").insert({
        "event_id": event_id,
        "student_id": current_user.id,
        "full_name": full_name,
        "email": email,
        "department": dept,
        "year": year,
        "phone": phone
    }).execute()

    flash("Registration successful!", "success")
    return redirect(url_for("event_detail", event_id=event_id))



@app.route("/organizer/event/<event_id>/registrations")
@login_required
def view_registrations(event_id):
    # Ensure logged in organizer owns the event
    event = supabase.table("events").select("*").eq("id", event_id).single().execute().data
    if event["organizer_id"] != current_user.id:
        flash("Not authorized!", "danger")
        return redirect(url_for("dashboard"))

    regs = supabase.table("registrations").select("*").eq("event_id", event_id).execute().data
    return render_template("view_registrations.html", regs=regs, event=event)


if __name__ == "__main__":
    app.run(debug=True)
