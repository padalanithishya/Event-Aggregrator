from wtforms.validators import Optional
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed
from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, IntegerField, StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField, BooleanField, FloatField, TimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from wtforms import SelectField

class StudentLoginForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email")
    ])

    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=4, message="Password must be at least 4 characters")
    ])

    submit = SubmitField("Login")


class StudentRegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    roll_number = StringField("Roll Number", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    college_name = StringField("College Name", validators=[DataRequired()])
    department = StringField("Department", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")


class OrganizerRegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    college_name = StringField("College Name", validators=[DataRequired()])
    department = StringField("Department", validators=[DataRequired()])
    club_name = StringField("Club Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    proof = FileField("Upload Proof (ID Card / Club Letter)", validators=[FileAllowed(['jpg','png','jpeg','pdf'],"Images/PDF only!")])
    submit = SubmitField("Register")


class OrganizerLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    secret_code = StringField("Secret Code", validators=[DataRequired()])
    submit = SubmitField("Login")


    
# 👨‍💻 Admin Login (simple)


# 🏁 Event Form
class EventForm(FlaskForm):
    title = StringField("Event Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    college_name = StringField("College Name", validators=[DataRequired()])
    event_type = SelectField("Event Type", choices=[("technical", "Technical"), ("cultural", "Cultural"), ("sports", "Sports"),("fest","Fest")], validators=[DataRequired()])
    mode = SelectField("Mode", choices=[("online", "Online"), ("offline", "Offline")], validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()], format='%Y-%m-%d')
    time = TimeField("Time", validators=[Optional()])
    venue = StringField("Venue", validators=[Optional()])
    registration_fee = DecimalField("Registration Fee", validators=[Optional()])
    seats = IntegerField("Available Seats", validators=[Optional()])  # ✅ ADD THIS
    image = FileField("Upload Event Image", validators=[Optional()])
    submit = SubmitField("Save Event")
    notice_letter = FileField("Upload Notice_letter", validators=[Optional()])




class RegisterEventForm(FlaskForm):
    student_name = StringField("Full Name", validators=[DataRequired()])
    roll_number = StringField("Roll Number", validators=[DataRequired()])
    college = StringField("College Name", validators=[DataRequired()])
    submit = SubmitField("Confirm Registration")




class AdminLoginForm(FlaskForm):
    email = StringField("Admin Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    secret_code = StringField("Admin Secret Code", validators=[DataRequired()])  # ✅ add this
    submit = SubmitField("Login as Admin")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField("Send Message")
