import streamlit as st
import sqlitecloud
import random
import uuid


def get_database_connection():
    conn = sqlitecloud.connect(
        "sqlitecloud://cxup3m3knz.sqlite.cloud:8860/industry_reg?apikey=ogQNaPUaDxZTJiTQEXlZGJB6zFAYqAkZdmzvJ3UpPrM"
    )
    return conn


# Create/connect to the database and create tables if not exists
def create_database_tables():
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    phone_number INTEGER UNIQUE,
                    industry_category TEXT,
                    state_ocmms_id TEXT,
                    num_stacks INTEGER
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS stacks (
                    stack_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    process_attached TEXT,
                    stack_condition TEXT,
                    stack_type TEXT,
                    cems_installed TEXT,
                    parameters TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS cems_instruments (
                    cems_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stack_id INTEGER,
                    parameter TEXT,
                    measuring_range_low REAL,
                    measuring_range_high REAL,
                    communication_protocol TEXT,
                    FOREIGN KEY (stack_id) REFERENCES stacks (stack_id)
                )""")
    conn.commit()
    conn.close()


# Add a new user record or fetch existing user
def add_user(phone_number):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE phone_number = ?", (phone_number,))
    existing_user = c.fetchone()

    if existing_user:
        user_id = existing_user[0]
    else:
        user_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO users (user_id, phone_number) VALUES (?, ?)",
            (user_id, phone_number),
        )
        conn.commit()

    conn.close()
    return user_id


# Update user details after form submission
def update_user_details(user_id, industry_category, state_ocmms_id, num_stacks):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """UPDATE users 
                 SET industry_category=?, state_ocmms_id=?, num_stacks=?
                 WHERE user_id=?""",
        (industry_category, state_ocmms_id, num_stacks, user_id),
    )
    conn.commit()
    conn.close()


# Page Initialization
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Login"
if "otp_sent" not in st.session_state:
    st.session_state["otp_sent"] = False
if "otp_verified" not in st.session_state:
    st.session_state["otp_verified"] = False

# Create the tables if not already present
create_database_tables()


# Function to change the current page
def set_page(page_name):
    st.session_state["current_page"] = page_name


# Callback for OTP verification
def verify_otp_callback(user_otp, correct_otp, phone_number):
    if user_otp == str(correct_otp):
        st.session_state["otp_verified"] = True
        user_id = add_user(phone_number)
        st.session_state["user_id"] = user_id
        set_page("Industry Details")
    else:
        st.error("Incorrect OTP. Please try again.")


# Define the Login Page
def login_page():
    st.header("Welcome! Please log in or sign up to continue.")
    phone_number = st.text_input("Enter your phone number", max_chars=10)
    st.session_state["phone_number"] = phone_number

    if st.button("Send OTP", key="send_otp") and phone_number:
        otp = random.randint(1000, 9999)
        st.session_state["otp"] = otp
        st.session_state["otp_sent"] = True
        st.success(f"OTP sent to {phone_number} (for testing, the OTP is {otp})")

    if st.session_state["otp_sent"]:
        user_otp = st.text_input("Enter the OTP you received", max_chars=4)
        st.button(
            "Verify OTP",
            on_click=verify_otp_callback,
            args=(user_otp, st.session_state["otp"], phone_number),
        )


# Define the Industry Details Page
def industry_details_page():
    st.header("Industry Basic Details")
    industry_category = st.text_input("Industry Category")
    state_ocmms_id = st.text_input("State OCMMS ID")
    num_stacks = st.number_input("Number of Stacks", min_value=1, step=1)
    user_id = st.session_state.get("user_id", "")

    if st.button("Submit Industry Details", key="submit_industry"):
        update_user_details(user_id, industry_category, state_ocmms_id, num_stacks)
        st.success("Industry details submitted successfully!")
        st.session_state["current_page"] = "Stack Details"  # Move to the next page


# Render Pages Based on Session State
if st.session_state["current_page"] == "Login":
    login_page()
elif (
    st.session_state["current_page"] == "Industry Details"
    and st.session_state["otp_verified"]
):
    industry_details_page()
