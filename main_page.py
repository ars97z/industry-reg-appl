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
                    industry_name TEXT,
                    address TEXT,
                    state TEXT,
                    district TEXT,
                    production_capacity TEXT,
                    num_stacks INTEGER,
                    industry_environment_head TEXT,
                    industry_instrument_head TEXT,
                    concerned_person_cems TEXT,
                    industry_email TEXT
                )""")
    # Create stacks table with foreign key to users table
    c.execute("""CREATE TABLE IF NOT EXISTS stacks (
                        stack_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        process_attached TEXT,
                        apcd_details TEXT,
                        latitude REAL,
                        longitude REAL,
                        stack_condition TEXT,
                        stack_shape TEXT,
                        diameter REAL,
                        length REAL,
                        width REAL,
                        stack_material TEXT,
                        stack_height REAL,
                        platform_height REAL,
                        platform_approachable TEXT,
                        cems_installed TEXT,
                        follows_formula TEXT,
                        manual_port_installed TEXT,
                        cems_below_manual TEXT,
                        parameters TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )""")

    # Create cems_instruments table with foreign key to stacks table
    c.execute("""CREATE TABLE IF NOT EXISTS cems_instruments (
                    cems_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stack_id INTEGER,
                    parameter TEXT,
                    make TEXT,
                    model TEXT,
                    serial_number TEXT,
                    measuring_range_low REAL,
                    measuring_range_high REAL,
                    certified TEXT,
                    certification_agency TEXT,
                    communication_protocol TEXT,
                    measurement_method TEXT,
                    technology TEXT,
                    connected_bspcb TEXT,
                    connected_cpcb TEXT,
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
if "current_param_index" not in st.session_state:
    st.session_state["current_param_index"] = 0

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
    st.title("🌳 Industry Registration Portal")
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
    st.title("🌳 Industry Registration Portal")
    st.header("Industry Basic Details")

    industry_category = st.text_input("Industry Category")
    state_ocmms_id = st.text_input("State OCMMS ID")
    industry_name = st.text_input("Industry Name")
    address = st.text_area("Address")
    state = st.text_input("State")
    district = st.text_input("District")
    production_capacity = st.text_input("Production Capacity")
    num_stacks = st.number_input("Number of Stacks", min_value=1, step=1)
    industry_environment_head = st.text_input("Industry Environment Head")
    industry_instrument_head = st.text_input("Industry Instrument Head")
    concerned_person_cems = st.text_input("Concerned Person for CEMS")
    industry_email = st.text_input("Industry Representative Email ID")

    user_id = st.session_state.get("user_id", "")

    def submit_industry_details():
        update_user_details(
            user_id,
            industry_category,
            state_ocmms_id,
            industry_name,
            address,
            state,
            district,
            production_capacity,
            num_stacks,
            industry_environment_head,
            industry_instrument_head,
            concerned_person_cems,
            industry_email,
        )
        st.session_state["num_stacks"] = num_stacks
        st.session_state["current_page"] = "Stack Details"

    st.button("Submit Industry Details", on_click=submit_industry_details)


def update_user_details(
    user_id,
    industry_category,
    state_ocmms_id,
    industry_name,
    address,
    state,
    district,
    production_capacity,
    num_stacks,
    industry_environment_head,
    industry_instrument_head,
    concerned_person_cems,
    industry_email,
):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """UPDATE users 
           SET industry_category=?, state_ocmms_id=?, industry_name=?, address=?, 
               state=?, district=?, production_capacity=?, num_stacks=?, 
               industry_environment_head=?, industry_instrument_head=?, 
               concerned_person_cems=?, industry_email=? 
           WHERE user_id=?""",
        (
            industry_category,
            state_ocmms_id,
            industry_name,
            address,
            state,
            district,
            production_capacity,
            num_stacks,
            industry_environment_head,
            industry_instrument_head,
            concerned_person_cems,
            industry_email,
            user_id,
        ),
    )
    conn.commit()
    conn.close()


def stack_details_page():
    st.title("🌳 Industry Registration Portal")
    st.subheader(
        f"Stack Details - Stack {st.session_state['current_stack']} of {st.session_state['num_stacks']}"
    )

    # Get user_id from session state
    user_id = st.session_state.get("user_id", "")

    # Input fields for stack details
    process_attached = st.text_input("Process Attached")
    apcd_details = st.text_input("APCD Details")
    latitude = st.number_input("Latitude", format="%.6f")
    longitude = st.number_input("Longitude", format="%.6f")
    stack_condition = st.selectbox("Stack Condition", ["Wet", "Dry"])

    stack_shape = st.selectbox(
        "Is it a Circular Stack/Rectangular Stack?", ["Circular", "Rectangular"]
    )
    if stack_shape == "Circular":
        diameter = st.number_input("Diameter (in meters)", min_value=0.0)
        length, width = None, None
    else:
        length = st.number_input("Length (in meters)", min_value=0.0)
        width = st.number_input("Width (in meters)", min_value=0.0)
        diameter = None

    stack_material = st.text_input("Stack Construction Material")
    stack_height = st.number_input("Stack Height (in meters)", min_value=0.0)
    platform_height = st.number_input(
        "Platform for Manual Monitoring Height (in meters)", min_value=0.0
    )
    platform_approachable = st.selectbox("Is Platform Approachable?", ["Yes", "No"])

    cems_installed = st.selectbox(
        "Where is CEMS Installed?", ["A. Stack/Chimney", "B. Duct", "C. Both"]
    )
    follows_formula = st.selectbox(
        "Does the Installation Follow 8D/2D Formula?", ["Yes", "No"]
    )
    manual_port_installed = st.selectbox(
        "Has a Manual Monitoring Port Been Installed in the Duct?", ["Yes", "No"]
    )
    cems_below_manual = st.selectbox(
        "Is CEMS Installation Point at Least 500mm Below the Manual Monitoring Point?",
        ["Yes", "No"],
    )

    parameters = st.multiselect(
        "Parameters to be Monitored",
        ["PM", "SOx", "NOx", "O2", "HCL", "HF", "CL2", "others"],
    )

    # Define the function before it is referenced
    def submit_stack_details():
        # Add stack details to the database
        stack_id = add_stack(
            user_id=user_id,
            process_attached=process_attached,
            apcd_details=apcd_details,
            latitude=latitude,
            longitude=longitude,
            stack_condition=stack_condition,
            stack_shape=stack_shape,
            diameter=diameter,
            length=length,
            width=width,
            stack_material=stack_material,
            stack_height=stack_height,
            platform_height=platform_height,
            platform_approachable=platform_approachable,
            cems_installed=cems_installed,
            follows_formula=follows_formula,
            manual_port_installed=manual_port_installed,
            cems_below_manual=cems_below_manual,
            parameters=",".join(parameters),
        )

        # Update session state for navigation
        st.session_state["current_stack_id"] = stack_id
        st.session_state["selected_parameters"] = (
            parameters  # Store parameters for CEMS instrument details
        )
        st.session_state["current_page"] = "CEMS Instrument Details"
        st.session_state["current_param_index"] = 0

    st.button("Submit Stack Details", on_click=submit_stack_details)


def add_stack(user_id, **stack_details):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO stacks (user_id, process_attached, apcd_details, latitude, longitude, 
                               stack_condition, stack_shape, diameter, length, width, 
                               stack_material, stack_height, platform_height, 
                               platform_approachable, cems_installed, follows_formula, 
                               manual_port_installed, cems_below_manual, parameters) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            stack_details.get("process_attached"),
            stack_details.get("apcd_details"),
            stack_details.get("latitude"),
            stack_details.get("longitude"),
            stack_details.get("stack_condition"),
            stack_details.get("stack_shape"),
            stack_details.get("diameter"),
            stack_details.get("length"),
            stack_details.get("width"),
            stack_details.get("stack_material"),
            stack_details.get("stack_height"),
            stack_details.get("platform_height"),
            stack_details.get("platform_approachable"),
            stack_details.get("cems_installed"),
            stack_details.get("follows_formula"),
            stack_details.get("manual_port_installed"),
            stack_details.get("cems_below_manual"),
            stack_details.get("parameters"),
        ),
    )
    stack_id = c.lastrowid
    conn.commit()
    conn.close()
    return stack_id


# Define the CEMS Instrument Details Page
def cems_instrument_details_page():
    st.title("🌳 Industry Registration Portal")
    st.subheader(
        f"CEMS Instrument Details for Stack {st.session_state['current_stack']} of {st.session_state['num_stacks']}"
    )

    # Fetch the selected parameters from Stack Details
    parameters_list = st.session_state.get("selected_parameters", [])

    # Sort parameters based on the desired sequence (PM, SO2, NOx)
    parameter_priority = {
        "PM": 1,
        "SOx": 2,
        "NOx": 3,
        "HCL": 4,
        "HF": 5,
        "CL2": 6,
        "O2": 7,
        "others": 8,
    }
    sorted_parameters = sorted(
        parameters_list, key=lambda param: parameter_priority.get(param, 100)
    )

    # Get the current parameter to process
    current_param_index = st.session_state.get("current_param_index", 0)

    if current_param_index < len(sorted_parameters):
        parameter = sorted_parameters[current_param_index]
        st.write(f"Current Parameter: **{parameter}**")

        # Input fields for the current parameter's CEMS instrument details
        make = st.text_input("Make")
        model = st.text_input("Model")
        serial_number = st.text_input("Serial Number")
        measuring_range_low = st.number_input("Measuring Range Low", min_value=0.0)
        measuring_range_high = st.number_input("Measuring Range High", min_value=0.0)
        certified = st.selectbox("Certified?", ["Yes", "No"])
        certification_agency = st.text_input("Certification Agency Name")
        communication_protocol = st.selectbox(
            "Default Communication Protocol", ["4-20 mA", "RS-485", "RS-423"]
        )
        measurement_method = st.selectbox(
            "Measurement Method", ["In-situ", "Extractive"]
        )
        technology = st.text_input("Technology")
        connected_bspcb = st.selectbox(
            "Is it connected with BSPCB Server?", ["Yes", "No"]
        )
        connected_cpcb = st.selectbox(
            "Is it connected with CPCB Server?", ["Yes", "No"]
        )

        # Function to submit the CEMS instrument details for the current parameter
        def submit_cems_instrument_details():
            stack_id = st.session_state.get("current_stack_id", "")

            add_cems_instrument(
                stack_id=stack_id,
                parameter=parameter,
                make=make,
                model=model,
                serial_number=serial_number,
                measuring_range_low=measuring_range_low,
                measuring_range_high=measuring_range_high,
                certified=certified,
                certification_agency=certification_agency,
                communication_protocol=communication_protocol,
                measurement_method=measurement_method,
                technology=technology,
                connected_bspcb=connected_bspcb,
                connected_cpcb=connected_cpcb,
            )

            # Move to the next parameter
            st.session_state["current_param_index"] += 1

            # Update the current page
            if st.session_state["current_param_index"] >= len(sorted_parameters):
                st.session_state["current_param_index"] = 0
                st.session_state["current_stack"] += 1
                st.session_state["current_page"] = (
                    "Stack Details"
                    if st.session_state["current_stack"]
                    <= st.session_state["num_stacks"]
                    else "Registration Complete"
                )
            else:
                st.session_state["current_page"] = "CEMS Instrument Details"

            st.session_state["current_rerun_trigger"] = True

        # Submit button for the current parameter
        st.button(
            "Submit CEMS Instrument Details", on_click=submit_cems_instrument_details
        )

    else:
        st.write("All parameters for this stack have been processed.")
        st.session_state["current_param_index"] = 0  # Reset parameter index
        st.session_state["current_stack"] += 1  # Move to next stack

        # Navigate to the next stack or complete registration
        st.session_state["current_page"] = (
            "Stack Details"
            if st.session_state["current_stack"] <= st.session_state["num_stacks"]
            else "Registration Complete"
        )


def add_cems_instrument(stack_id, **instrument_details):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO cems_instruments (
            stack_id, parameter, make, model, serial_number, 
            measuring_range_low, measuring_range_high, certified, 
            certification_agency, communication_protocol, measurement_method, 
            technology, connected_bspcb, connected_cpcb
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            stack_id,
            instrument_details.get("parameter"),
            instrument_details.get("make"),
            instrument_details.get("model"),
            instrument_details.get("serial_number"),
            instrument_details.get("measuring_range_low"),
            instrument_details.get("measuring_range_high"),
            instrument_details.get("certified"),
            instrument_details.get("certification_agency"),
            instrument_details.get("communication_protocol"),
            instrument_details.get("measurement_method"),
            instrument_details.get("technology"),
            instrument_details.get("connected_bspcb"),
            instrument_details.get("connected_cpcb"),
        ),
    )
    conn.commit()
    conn.close()


# Define the Registration Complete Page
def registration_complete_page():
    st.title("🌳 Industry Registration Portal")
    st.subheader("Registration Complete")
    st.write("Thank you for registering. Your details have been successfully saved.")


# Render pages based on the current state
if st.session_state["current_page"] == "Login":
    login_page()
elif st.session_state["current_page"] == "Industry Details" and st.session_state.get(
    "otp_verified", False
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
