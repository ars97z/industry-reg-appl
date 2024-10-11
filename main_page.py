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
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE phone_number = ?", (phone_number,))
    existing_user = c.fetchone()

    if existing_user:
        user_id = existing_user[0]  # Retrieve the existing user_id
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


# Initialize session states
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Login"
if "otp_sent" not in st.session_state:
    st.session_state["otp_sent"] = False
if "otp_verified" not in st.session_state:
    st.session_state["otp_verified"] = False
if "submit_industry" not in st.session_state:
    st.session_state["submit_industry"] = False
if "submit_stack" not in st.session_state:
    st.session_state["submit_stack"] = False

# Create database tables
create_database_tables()


# Streamlit App - Navigation and Pages
st.title("🌿 Industry Registration Portal")

# Login Page
if st.session_state["current_page"] == "Login":
    st.header("Welcome! Please log in or sign up to continue.")
    phone_number = st.text_input("Enter your phone number", value="", max_chars=10)
    st.session_state["phone_number"] = phone_number

    if st.button("Send OTP", key="send_otp"):
        if phone_number:
            otp = random.randint(1000, 9999)
            st.session_state["otp"] = otp
            st.session_state["otp_sent"] = True
            st.success(f"OTP sent to {phone_number} (for testing, the OTP is {otp})")
        else:
            st.error("Please enter a valid phone number.")

    if st.session_state["otp_sent"]:
        user_otp = st.text_input("Enter the OTP you received", value="", max_chars=4)
        if st.button("Verify OTP", key="verify_otp"):
            if user_otp == str(st.session_state["otp"]):
                st.session_state["otp_verified"] = True
                user_id = add_user(phone_number)
                st.session_state["user_id"] = user_id
                st.session_state["current_page"] = "Industry Details"
                st.success("OTP Verified!")
            else:
                st.error("Incorrect OTP. Please try again.")

# Industry Details Page
if (
    st.session_state["current_page"] == "Industry Details"
    and st.session_state["otp_verified"]
):
    st.header("Industry Basic Details")
    user_id = st.session_state["user_id"]

    industry_category = st.text_input("Industry Category")
    state_ocmms_id = st.text_input("State OCMMS ID")
    num_stacks = st.number_input("Number of Stacks", min_value=1)

    if st.button("Submit Industry Details", key="submit_industry"):
        update_user_details(user_id, industry_category, state_ocmms_id, num_stacks)
        st.session_state["num_stacks"] = num_stacks
        st.session_state["current_stack"] = 1
        st.session_state["current_page"] = "Stack Details"
        st.success("Industry details submitted successfully!")

# Stack Details Page
if (
    st.session_state["current_page"] == "Stack Details"
    and st.session_state["submit_industry"]
):
    st.header(
        f"Stack Details - Stack {st.session_state['current_stack']} of {st.session_state['num_stacks']}"
    )
    user_id = st.session_state["user_id"]

    process_attached = st.text_input("Process Attached")
    stack_condition = st.selectbox("Stack Condition", ["Wet", "Dry"])
    stack_type = st.selectbox("Stack Type", ["Circular", "Rectangular"])
    cems_installed = st.selectbox("CEMS Installed?", ["Yes", "No"])
    parameters = st.text_area("Parameters to Monitor")

    if st.button(
        "Submit Stack Details", key=f"submit_stack_{st.session_state['current_stack']}"
    ):
        # Add stack details here...
        st.session_state["submit_stack"] = True
        if st.session_state["current_stack"] < st.session_state["num_stacks"]:
            st.session_state["current_stack"] += 1
        else:
            st.session_state["current_page"] = "Registration Complete"
        st.success("Stack details submitted successfully!")

# Registration Complete Page
if (
    st.session_state["current_page"] == "Registration Complete"
    and st.session_state["submit_stack"]
):
    st.header("Registration Complete")
    st.success("Thank you for registering. Your details have been successfully saved.")
    st.info("You can now exit or start a new registration if needed.")
