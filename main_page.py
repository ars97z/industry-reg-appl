import streamlit as st
import sqlitecloud
import random
import uuid


def get_database_connection():
    # Include the database name directly in the connection string
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
                    phone_number TEXT UNIQUE,
                    industry_category TEXT,
                    state_ocmms_id TEXT,
                    industry_name TEXT,
                    address TEXT,
                    state TEXT,
                    district TEXT,
                    production_capacity INTEGER,
                    num_stacks INTEGER,
                    env_head TEXT,
                    instrument_head TEXT,
                    cems_person TEXT,
                    representative_email TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS stacks (
                    stack_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    process_attached TEXT,
                    apcd_details TEXT,
                    latitude REAL,
                    longitude REAL,
                    stack_condition TEXT,
                    stack_type TEXT,
                    diameter REAL,
                    length REAL,
                    width REAL,
                    construction_material TEXT,
                    stack_height REAL,
                    platform_height REAL,
                    platform_accessibility TEXT,
                    cems_installed TEXT,
                    compliance_8d_2d TEXT,
                    monitoring_port_installed TEXT,
                    cems_below_monitoring TEXT,
                    parameters TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )""")
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
                    certification_agency_name TEXT,
                    communication_protocol TEXT,
                    measurement_method TEXT,
                    technology TEXT,
                    connected_bspcb TEXT,
                    connected_cpcb TEXT,
                    FOREIGN KEY (stack_id) REFERENCES stacks (stack_id)
                )""")
    conn.commit()
    conn.close()


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


# Update user details after form submission
def update_user_details(user_id, **details):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """UPDATE users 
                 SET industry_category=?, state_ocmms_id=?, industry_name=?, address=?, state=?, 
                     district=?, production_capacity=?, num_stacks=?, env_head=?, 
                     instrument_head=?, cems_person=?, representative_email=?
                 WHERE user_id=?""",
        (*details.values(), user_id),
    )
    conn.commit()
    conn.close()


# Add stack details to the database
def add_stack_details(user_id, **stack_details):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO stacks (
                    user_id, process_attached, apcd_details, latitude, longitude, stack_condition, 
                    stack_type, diameter, length, width, construction_material, stack_height, 
                    platform_height, platform_accessibility, cems_installed, compliance_8d_2d, 
                    monitoring_port_installed, cems_below_monitoring, parameters
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, *stack_details.values()),
    )
    stack_id = c.lastrowid
    conn.commit()
    conn.close()
    return stack_id


# Add CEMS instrument details to the database
def add_cems_details(stack_id, **cems_details):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO cems_instruments (
                    stack_id, parameter, make, model, serial_number, measuring_range_low, 
                    measuring_range_high, certified, certification_agency_name, communication_protocol, 
                    measurement_method, technology, connected_bspcb, connected_cpcb
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (stack_id, *cems_details.values()),
    )
    conn.commit()
    conn.close()


# Simulate OTP sending
def send_otp(phone_number):
    otp = random.randint(1000, 9999)
    st.session_state["otp"] = otp
    st.session_state["otp_sent"] = True
    st.session_state["otp_verified"] = False
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


# Initialize session states
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Login or Sign Up"

# Create database tables
create_database_tables()

# Streamlit App - Navigation and Pages
st.title("🌿 Industry Registration Portal")

# Navigation logic based on the current page
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

# Industry Details Page
if st.session_state["current_page"] == "Industry Details":
    st.header("Industry Basic Details")
    user_id = st.session_state.get("user_id", "")

    industry_category = st.text_input("Industry Category")
    state_ocmms_id = st.text_input("State OCMMS ID")
    industry_name = st.text_input("Industry Name")
    address = st.text_area("Address")
    state = st.text_input("State")
    district = st.text_input("District")
    production_capacity = st.number_input("Production Capacity", min_value=0)
    num_stacks = st.number_input("Number of Stacks", min_value=1)
    env_head = st.text_input("Industry Environment Head")
    instrument_head = st.text_input("Industry Instrument Head")
    cems_person = st.text_input("Concerned Person for CEMS")
    representative_email = st.text_input("Industry Representative Email ID")

    if st.button("Submit Industry Details"):
        update_user_details(
            user_id,
            industry_category=industry_category,
            state_ocmms_id=state_ocmms_id,
            industry_name=industry_name,
            address=address,
            state=state,
            district=district,
            production_capacity=production_capacity,
            num_stacks=num_stacks,
            env_head=env_head,
            instrument_head=instrument_head,
            cems_person=cems_person,
            representative_email=representative_email,
        )
        st.session_state["num_stacks"] = num_stacks
        st.session_state["current_stack"] = 1
        st.session_state["current_page"] = "Stack Details"

# Stack Details Page
if st.session_state["current_page"] == "Stack Details":
    st.header(
        f"Stack Details - Stack {st.session_state['current_stack']} of {st.session_state['num_stacks']}"
    )
    user_id = st.session_state.get("user_id", "")

    process_attached = st.text_input("Process Attached")
    apcd_details = st.text_input("APCD Details")
    latitude = st.number_input("Latitude")
    longitude = st.number_input("Longitude")
    stack_condition = st.selectbox("Stack Condition", ["Wet", "Dry"])
    stack_type = st.selectbox(
        "Is it a Circular Stack/Rectangular Stack", ["Circular", "Rectangular"]
    )
    diameter = (
        st.number_input("Diameter (if Circular)", key="diameter")
        if stack_type == "Circular"
        else None
    )
    length = (
        st.number_input("Length (if Rectangular)", key="length")
        if stack_type == "Rectangular"
        else None
    )
    width = (
        st.number_input("Width (if Rectangular)", key="width")
        if stack_type == "Rectangular"
        else None
    )
    construction_material = st.text_input("Stack Construction Material")
    stack_height = st.number_input("Stack Height (in meters)")
    platform_height = st.number_input(
        "Platform for Manual Monitoring Location Height from Ground (in meters)"
    )
    platform_accessibility = st.selectbox(
        "Is Platform Approachable?",
        [
            "Yes - Ladder",
            "Yes - Lift",
            "Yes - Staircase",
            "No - Must be Approachable, Follow CPCB Guidelines",
        ],
    )
    cems_installed = st.selectbox(
        "Where is CEMS Installed?", ["Stack/Chimney", "Duct", "Both"]
    )
    compliance_8d_2d = st.selectbox(
        "Does the Installation Follow 8D/2D Formula?",
        ["Yes", "No - Refer CPCB Guidelines"],
    )
    monitoring_port_installed = st.selectbox(
        "Has a Manual Monitoring Port Been Installed in the Duct?",
        ["Yes", "No - Refer CPCB Guidelines"],
    )
    cems_below_monitoring = st.selectbox(
        "Is CEMS Installation Point at Least 500mm Below the Manual Monitoring Point?",
        ["Yes", "No - Refer CPCB Guidelines"],
    )
    parameters = st.text_area("What are the Parameters Required to be Monitored?")

    if st.button("Submit Stack Details"):
        stack_id = add_stack_details(
            user_id=user_id,
            process_attached=process_attached,
            apcd_details=apcd_details,
            latitude=latitude,
            longitude=longitude,
            stack_condition=stack_condition,
            stack_type=stack_type,
            diameter=diameter,
            length=length,
            width=width,
            construction_material=construction_material,
            stack_height=stack_height,
            platform_height=platform_height,
            platform_accessibility=platform_accessibility,
            cems_installed=cems_installed,
            compliance_8d_2d=compliance_8d_2d,
            monitoring_port_installed=monitoring_port_installed,
            cems_below_monitoring=cems_below_monitoring,
            parameters=parameters,
        )
        st.session_state["stack_id"] = stack_id
        st.session_state["current_page"] = "CEMS Instrument Details"
        st.success("Stack details submitted successfully!")

# CEMS Instrument Details Page
if st.session_state["current_page"] == "CEMS Instrument Details":
    st.header(
        f"CEMS Instrument Details for Stack {st.session_state['current_stack']} of {st.session_state['num_stacks']}"
    )
    stack_id = st.session_state.get("stack_id")

    parameters = st.multiselect(
        "Select Parameters",
        ["PM", "SOx", "NOx", "HCL", "HF", "Cl2", "O2", "Others"],
        key=f"parameters_{st.session_state['current_stack']}",
    )

    for parameter in parameters:
        st.markdown(f"### Details for Parameter: {parameter}")
        make = st.text_input(f"Make for {parameter}", key=f"make_{parameter}")
        model = st.text_input(f"Model for {parameter}", key=f"model_{parameter}")
        serial_number = st.text_input(
            f"Serial Number for {parameter}", key=f"serial_{parameter}"
        )
        measuring_range_low = st.number_input(
            f"Measuring Range Low for {parameter}",
            min_value=0.0,
            key=f"range_low_{parameter}",
        )
        measuring_range_high = st.number_input(
            f"Measuring Range High for {parameter}",
            min_value=measuring_range_low,
            key=f"range_high_{parameter}",
        )
        certified = st.selectbox(
            f"Certified for {parameter}", ["YES", "NO"], key=f"certified_{parameter}"
        )
        certification_agency_name = st.text_input(
            f"Certification Agency Name for {parameter}", key=f"agency_{parameter}"
        )
        communication_protocol = st.selectbox(
            f"Default Communication Protocol for {parameter}",
            ["4-20 mA", "RS-485", "RS-423"],
            key=f"protocol_{parameter}",
        )
        measurement_method = st.selectbox(
            f"Measurement Method for {parameter}",
            ["In-situ", "Extractive"],
            key=f"method_{parameter}",
        )
        technology = st.text_input(
            f"Technology for {parameter}", key=f"technology_{parameter}"
        )
        connected_bspcb = st.selectbox(
            f"Connected to BSPCB Server for {parameter}",
            ["YES", "NO"],
            key=f"bspcb_{parameter}",
        )
        connected_cpcb = st.selectbox(
            f"Connected to CPCB Server for {parameter}",
            ["YES", "NO"],
            key=f"cpcb_{parameter}",
        )

        if st.button(
            f"Submit CEMS Details for {parameter}", key=f"submit_cems_{parameter}"
        ):
            add_cems_details(
                stack_id=stack_id,
                parameter=parameter,
                make=make,
                model=model,
                serial_number=serial_number,
                measuring_range_low=measuring_range_low,
                measuring_range_high=measuring_range_high,
                certified=certified,
                certification_agency_name=certification_agency_name,
                communication_protocol=communication_protocol,
                measurement_method=measurement_method,
                technology=technology,
                connected_bspcb=connected_bspcb,
                connected_cpcb=connected_cpcb,
            )
            st.success(f"CEMS details for {parameter} submitted successfully!")

    # Complete CEMS details for the current stack and navigate accordingly
    if st.button("Complete CEMS Details"):
        if st.session_state["current_stack"] < st.session_state["num_stacks"]:
            st.session_state["current_stack"] += 1
            st.session_state["current_page"] = "Stack Details"
            st.success("Proceeding to the next stack.")
        else:
            st.session_state["current_page"] = "Registration Complete"
            st.success("All details submitted. Registration is complete.")

# Registration Complete Page
if st.session_state["current_page"] == "Registration Complete":
    st.header("Registration Complete")
    st.success("Thank you for registering. Your details have been successfully saved.")
    st.info("You can now exit or start a new registration if needed.")
