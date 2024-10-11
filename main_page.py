import streamlit as st
import sqlitecloud
import random
import uuid


def get_database_connection():
    conn = sqlitecloud.connect(
        "sqlitecloud://cxup3m3knz.sqlite.cloud:8860/industry_reg?apikey=kLsCEWPNnKJe6SrMuMBCP2Ijpbf5yJwjLS8AlEiihAE"
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


# Initialize the database tables
# create_database_tables()


# Simulate OTP sending
def send_otp(phone_number):
    otp = random.randint(1000, 9999)
    st.session_state["otp"] = otp
    st.session_state["otp_sent"] = True
    st.success(f"OTP sent to {phone_number} (for testing, the OTP is {otp})")


# Verify OTP
def verify_otp(user_otp):
    if "otp" in st.session_state and user_otp == str(st.session_state["otp"]):
        st.session_state["otp_verified"] = True
        st.success("OTP Verified!")
        user_id = add_user(st.session_state["phone_number"])
        st.session_state["user_id"] = user_id
        st.session_state["current_page"] = "Industry Details"
    else:
        st.error("Incorrect OTP. Please try again.")


# Add a new user record after OTP verification
def add_user(phone_number):
    user_id = str(uuid.uuid4())
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (user_id, phone_number) VALUES (?, ?)",
        (user_id, phone_number),
    )
    conn.commit()
    conn.close()
    return user_id


# Initialize session states
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Login or Sign Up"
if "otp_sent" not in st.session_state:
    st.session_state["otp_sent"] = False
if "otp_verified" not in st.session_state:
    st.session_state["otp_verified"] = False

# Streamlit App - User Sign-Up and OTP Verification
st.title("🌿 Industry Registration Portal")

# Login or Sign Up Page
if st.session_state["current_page"] == "Login or Sign Up":
    st.header("Welcome! Please log in or sign up to continue.")
    phone_number = st.text_input("Enter your phone number", value="", max_chars=10)
    st.session_state["phone_number"] = phone_number

    if st.button("Send OTP"):
        if phone_number:
            send_otp(phone_number)
        else:
            st.error("Please enter a valid phone number.")

    if st.session_state.get("otp_sent"):
        user_otp = st.text_input("Enter the OTP you received", value="", max_chars=4)
        if st.button("Verify OTP"):
            verify_otp(user_otp)
