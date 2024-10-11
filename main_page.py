import streamlit as st
import sqlitecloud
import random
import uuid


# Database connection and setup
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


# Update user details
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


# Add stack details
def add_stack_details(
    user_id, process_attached, stack_condition, stack_type, cems_installed, parameters
):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO stacks (user_id, process_attached, stack_condition, stack_type, cems_installed, parameters)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            process_attached,
            stack_condition,
            stack_type,
            cems_installed,
            parameters,
        ),
    )
    stack_id = c.lastrowid
    conn.commit()
    conn.close()
    return stack_id


# Add CEMS instrument details
def add_cems_details(stack_id, parameter, measuring_range_low, measuring_range_high):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO cems_instruments (stack_id, parameter, measuring_range_low, measuring_range_high)
           VALUES (?, ?, ?, ?)""",
        (stack_id, parameter, measuring_range_low, measuring_range_high),
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
if "current_stack" not in st.session_state:
    st.session_state["current_stack"] = 1

# Create the tables if not already present
create_database_tables()


# Function to change the current page
def navigate_to(page_name):
    st.session_state["current_page"] = page_name
    st.experimental_rerun()


# Login Page
def login_page():
    st.header("Welcome! Please log in or sign up to continue.")
    phone_number = st.text_input("Enter your phone number", max_chars=10)
    st.session_state["phone_number"] = phone_number

    if st.button("Send OTP", key="send_otp"):
        if phone_number:
            otp = random.randint(1000, 9999)
            st.session_state["otp"] = str(otp)
            st.session_state["otp_sent"] = True
            st.success(f"OTP sent to {phone_number} (for testing, the OTP is {otp})")

    if st.session_state["otp_sent"]:
        user_otp = st.text_input("Enter the OTP you received", max_chars=4)
        if st.button("Verify OTP", key="verify_otp"):
            if user_otp == st.session_state["otp"]:
                st.session_state["otp_verified"] = True
                user_id = add_user(phone_number)
                st.session_state["user_id"] = user_id
                navigate_to("Industry Details")
            else:
                st.error("Incorrect OTP. Please try again.")


# Define the Industry Details Page
def industry_details_page():
    st.header("Industry Basic Details")
    industry_category = st.text_input("Industry Category")
    state_ocmms_id = st.text_input("State OCMMS ID")
    num_stacks = st.number_input("Number of Stacks", min_value=1, step=1)
    user_id = st.session_state.get("user_id", "")

    if st.button("Submit Industry Details", key="submit_industry"):
        update_user_details(user_id, industry_category, state_ocmms_id, num_stacks)
        st.session_state["num_stacks"] = num_stacks
        navigate_to("Stack Details")


# Define the Stack Details Page
def stack_details_page():
    st.header(f"Stack Details - Stack {st.session_state['current_stack']}")
    process_attached = st.text_input("Process Attached")
    stack_condition = st.selectbox("Stack Condition", ["Wet", "Dry"])
    stack_type = st.selectbox("Stack Type", ["Circular", "Rectangular"])
    cems_installed = st.selectbox(
        "Where is CEMS Installed?", ["Stack/Chimney", "Duct", "Both"]
    )
    parameters = st.multiselect(
        "Select parameters (e.g., PM2.5, SOx)", ["PM2.5", "SOx", "NOx", "CO2", "O2"]
    )

    user_id = st.session_state["user_id"]
    if st.button("Submit Stack Details", key="submit_stack"):
        stack_id = add_stack_details(
            user_id,
            process_attached,
            stack_condition,
            stack_type,
            cems_installed,
            ", ".join(parameters),
        )
        st.session_state["stack_id"] = stack_id
        navigate_to("CEMS Instrument Details")


# Define the CEMS Instrument Details Page
def cems_instrument_details_page():
    st.header(f"CEMS Instrument Details for Stack {st.session_state['current_stack']}")
    stack_id = st.session_state["stack_id"]
    parameter = st.selectbox(
        "Enter parameter for this instrument (e.g., PM2.5, SOx)",
        ["PM2.5", "SOx", "NOx", "CO2", "O2", "VOC"],
    )
    measuring_range_low = st.number_input("Measuring Range Low", min_value=0.0)
    measuring_range_high = st.number_input(
        "Measuring Range High", min_value=measuring_range_low
    )

    if st.button("Submit CEMS Details"):
        add_cems_details(stack_id, parameter, measuring_range_low, measuring_range_high)
        st.success("CEMS instrument details submitted successfully!")

        if st.session_state["current_stack"] < st.session_state["num_stacks"]:
            st.session_state["current_stack"] += 1
            navigate_to("Stack Details")
        else:
            navigate_to("Registration Complete")


# Define the Registration Complete Page
def registration_complete_page():
    st.header("Registration Complete")
    st.success("Thank you for registering. Your details have been successfully saved.")


# Render Pages Based on Session State
if st.session_state["current_page"] == "Login":
    login_page()
elif (
    st.session_state["current_page"] == "Industry Details"
    and st.session_state["otp_verified"]
):
    industry_details_page()
elif st.session_state["current_page"] == "Stack Details":
    stack_details_page()
elif st.session_state["current_page"] == "CEMS Instrument Details":
    cems_instrument_details_page()
elif st.session_state["current_page"] == "Registration Complete":
    registration_complete_page()
