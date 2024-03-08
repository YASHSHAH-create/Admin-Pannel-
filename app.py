# main_app.py
from flask import Flask, render_template, request, redirect
from flask_mail import Mail, Message
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random

app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587  # Replace with your SMTP server port
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'yash11122er@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'djfj mmdt txfq iehf'  # Replace with your email password

mail = Mail(app)

# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("medlive.json", scope)
client = gspread.authorize(creds)

# Open the publicly accessible Google Sheet using its URL
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1l8jmwFUR2BaffAqD2fCYlxTKs_oSgAr0gZB5BXk9zIQ/edit#gid=0"
spreadsheet = client.open_by_url(spreadsheet_url)
sheet = spreadsheet.get_worksheet(0)  # Assuming you want to use the first worksheet

# Function to generate a random 6-digit ticket ID
def generate_ticket_id():
    return ''.join(random.choices('0123456789', k=6))

# Function to get row number based on Ticket ID
def get_row_number_by_ticket_id(ticket_id):
    try:
        cell = sheet.find(ticket_id)
        return cell.row
    except gspread.exceptions.CellNotFound:
        return None

# Route for the form
@app.route("/")
def index():
    return render_template("index.html")

# Route to handle form submission
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    number = request.form.get("number")
    email = request.form.get("email")
    query = request.form.get("query")
    sector = request.form.get("sector")

    # Generate a random 6-digit ticket ID
    ticket_id = generate_ticket_id()

    # Check if the sheet is empty (no data)
    if not sheet.get_all_records():
        # If empty, add a bold header row
        header_row = ["Name", "Number", "Email", "Query", "Sector", "Ticket ID"]
        sheet.insert_row(header_row, 1)
        # Set bold formatting for the header row
        header_format = {
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER"
        }
        sheet.format("A1:F1", header_format)

    # Add data to Google Sheet
    data = [name, number, email, query, sector, ticket_id]
    sheet.append_row(data)

    # Send email to the provided email address
    send_email(email, ticket_id)

    # Redirect to a new page displaying the ticket ID
    return redirect(f"/ticket/{ticket_id}")

# Route to display the ticket ID
@app.route("/ticket/<ticket_id>")
def show_ticket(ticket_id):
    return render_template("show_ticket.html", ticket_id=ticket_id)

# Function to send email
def send_email(recipient, ticket_id):
    with mail.record_messages() as outbox:
        msg = Message('Your Ticket ID', sender='yash111122er@gmail.com', recipients=[recipient])
        msg.body = f'Your ticket ID is: {ticket_id}'
        mail.send(msg)

    # Access the recorded messages and print details to the console
    for message in outbox:
        print(f"Email sent to: {message.recipients[0]}")
        print(f"Sent from: {message.sender}")
        print(f"Subject: {message.subject}")
        print(f"Body: {message.body}")

# Admin credentials (replace with your own)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin_password'

# Route for the admin panel login
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Retrieve data from the Google Sheet
            data = sheet.get_all_records()
            return render_template("admin_panel.html", data=data)
        else:
            return "Invalid credentials. Please try again."

    return render_template("admin_login.html")

# Route for editing an entry
@app.route("/edit/<ticket_id>", methods=["GET", "POST"])
def edit(ticket_id):
    # Fetch data for the given ticket_id
    row_number = get_row_number_by_ticket_id(ticket_id)
    if row_number is None:
        return "Ticket not found."

    if request.method == "POST":
        # Update the row in the Google Sheet
        updated_data = [
            request.form.get("name"),
            request.form.get("number"),
            request.form.get("email"),
            request.form.get("query"),
            request.form.get("sector"),
            ticket_id,
        ]
        sheet.update(f"A{row_number}:F{row_number}", [updated_data])

        # Redirect to the admin panel after editing
        return redirect("/admin")

    # Fetch existing data for pre-populating the edit form
    existing_data = sheet.row_values(row_number)
    return render_template("edit_.html", ticket_id=ticket_id, existing_data=existing_data)
# Route for deleting an entry
@app.route("/delete/<ticket_id>")
def delete(ticket_id):
    # Fetch data for the given ticket_id
    row_number = get_row_number_by_ticket_id(ticket_id)
    if row_number is None:
        return "Ticket not found."

    # Delete the row in the Google Sheet
    sheet.delete_rows(row_number)

    # Redirect to the admin panel after deletion
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
