import streamlit as st
import sqlitecloud
import random
import uuid


# Database connection and setup
def get_database_connection():
    conn = sqlitecloud.connect(
        "sqlitecloud://cxup3m3knz.sqlite.cloud:8860/industry_reg?apikey=BODYl6TBlYCPRh8BciJjTFGiPVQwTjlZOz1dA0ns9fk"
    )
    return conn


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
def set_page(page_name):
    st.session_state["current_page"] = page_name


# Callback for OTP verification
def verify_otp_callback():
    user_otp = st.session_state.get("user_otp", "").strip()
    stored_otp = str(st.session_state.get("otp", ""))
    if user_otp == stored_otp:
        st.session_state["otp_verified"] = True
        user_id = add_user(st.session_state["phone_number"])
        st.session_state["user_id"] = user_id
        st.session_state["current_page"] = "Industry Details"
    else:
        st.error("Incorrect OTP. Please try again.")


# Define the Login Page
def login_page():
    st.title("🌿 Industry Registration Portal")
    st.header("Welcome! Please log in or sign up to continue.")
    phone_number = st.text_input("Enter your phone number", value="", max_chars=10)
    st.session_state["phone_number"] = phone_number

    # Send OTP when the user clicks "Send OTP"
    if st.button("Send OTP", key="send_otp"):
        if phone_number:
            otp = random.randint(1000, 9999)
            st.session_state["otp"] = otp
            st.session_state["otp_sent"] = True
            st.success(f"OTP sent to {phone_number} (for testing, the OTP is {otp})")
        else:
            st.error("Please enter a valid phone number.")

    # Display OTP input field only if OTP is sent but not verified yet
    if st.session_state["otp_sent"] and not st.session_state["otp_verified"]:
        st.text_input("Enter the OTP you received", key="user_otp", max_chars=4)
        st.button(
            "Verify OTP",
            on_click=verify_otp_callback,
        )


# Define the Industry Details Page
def industry_details_page():
    st.title("🌿 Industry Registration Portal")
    st.header("Industry Basic Details")
    industry_category = st.text_input("Industry Category")
    state_ocmms_id = st.text_input("State OCMMS ID")
    num_stacks = st.number_input("Number of Stacks", min_value=1, step=1)
    user_id = st.session_state.get("user_id", "")

    def submit_industry_details():
        update_user_details(user_id, industry_category, state_ocmms_id, num_stacks)
        st.session_state["num_stacks"] = num_stacks
        st.session_state["current_page"] = "Stack Details"

    st.button("Submit Industry Details", on_click=submit_industry_details)


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


# Define the Stack Details Page
def stack_details_page():
    st.title("🌿 Industry Registration Portal")
    st.subheader(
        f"Stack Details - Stack {st.session_state['current_stack']} of {st.session_state['num_stacks']}"
    )
    user_id = st.session_state.get("user_id", "")

    process_attached = st.text_input("Process Attached")
    stack_condition = st.selectbox("Stack Condition", ["Good", "Needs Repair", "Poor"])
    stack_type = st.selectbox("Stack Type", ["Circular", "Rectangular"])
    cems_installed = st.selectbox("CEMS Installed", ["Yes", "No"])
    parameters = st.text_area("Parameters to be Monitored (e.g., PM, SOx, NOx)")

    def submit_stack_details():
        stack_id = add_stack(
            user_id=user_id,
            process_attached=process_attached,
            stack_condition=stack_condition,
            stack_type=stack_type,
            cems_installed=cems_installed,
            parameters=parameters,
        )
        st.session_state["current_stack_id"] = stack_id
        st.session_state["current_page"] = "CEMS Instrument Details"

    st.button("Submit Stack Details", on_click=submit_stack_details)


def add_stack(user_id, **stack_details):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO stacks (user_id, process_attached, stack_condition, stack_type, cems_installed, parameters) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            stack_details.get("process_attached"),
            stack_details.get("stack_condition"),
            stack_details.get("stack_type"),
            stack_details.get("cems_installed"),
            stack_details.get("parameters"),
        ),
    )
    stack_id = c.lastrowid
    conn.commit()
    conn.close()
    return stack_id


# Define the CEMS Instrument Details Page
def cems_instrument_details_page():
    st.title("🌿 Industry Registration Portal")
    st.subheader(
        f"CEMS Instrument Details for Stack {st.session_state['current_stack']} of {st.session_state['num_stacks']}"
    )

    stack_id = st.session_state.get("current_stack_id", "")
    parameter = st.text_input("Enter parameter for this instrument (e.g., PM2.5, SOx)")
    measuring_range_low = st.number_input("Measuring Range Low", min_value=0.0)
    measuring_range_high = st.number_input("Measuring Range High", min_value=0.0)

    def submit_cems_instrument_details():
        add_cems_instrument(
            stack_id=stack_id,
            parameter=parameter,
            measuring_range_low=measuring_range_low,
            measuring_range_high=measuring_range_high,
        )

        # Increment the current stack count
        st.session_state["current_stack"] += 1

        # If there are more stacks, go back to "Stack Details" for the next stack
        if st.session_state["current_stack"] <= st.session_state["num_stacks"]:
            st.session_state["current_page"] = "Stack Details"
        else:
            st.session_state["current_page"] = "Registration Complete"

    st.button("Submit CEMS Instrument Details", on_click=submit_cems_instrument_details)


def add_cems_instrument(stack_id, **cems_details):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO cems_instruments (stack_id, parameter, 
                                         measuring_range_low, measuring_range_high) 
           VALUES (?, ?, ?, ?)""",
        (
            stack_id,
            cems_details.get("parameter"),
            cems_details.get("measuring_range_low"),
            cems_details.get("measuring_range_high"),
        ),
    )
    conn.commit()
    conn.close()


# Define the Registration Complete Page
def registration_complete_page():
    st.title("🌿 Industry Registration Portal")
    st.subheader("Registration Complete")
    st.write("Thank you for registering. Your details have been successfully saved.")


# Render Pages Based on Session State
if st.session_state["current_page"] == "Login":
    login_page()
elif (
    st.session_state["current_page"] == "Industry Details"
    and st.session_state["otp_verified"]
):
    industry_details_page()
elif (
    st.session_state["current_page"] == "Stack Details"
    and st.session_state["current_stack"] <= st.session_state["num_stacks"]
):
    stack_details_page()
elif (
    st.session_state["current_page"] == "CEMS Instrument Details"
    and st.session_state["current_stack"] <= st.session_state["num_stacks"]
):
    cems_instrument_details_page()
elif st.session_state["current_page"] == "Registration Complete":
    registration_complete_page()
