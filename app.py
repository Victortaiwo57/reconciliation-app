#  --- Importing Neccessary Libraries ---
import os
import bcrypt
import logging
import mysql.connector
import pandas as pd
from datetime import datetime
from shiny import App, reactive, render, ui, Outputs, Inputs, Session, req


# --- Setup Logger ---
logger = logging.getLogger("ShinyAppLogger")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("app.log")
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

purchase_pending = reactive.value(False)
payment_pending = reactive.value(False)


# --- DB Connection ---
def get_connection():
    """
    The function establishes a connection with MYSQL Database
    with necessary logger
    """

    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
        logger.debug("Database connection established")
        return conn
    except Exception as e:
        logger.exception("Database connection error")
        raise



# --- UI Layout ---

def page_ui():
    """
    This function help display user interface using shiny integration
    """

    return ui.navset_card_tab(
        ui.nav_panel("Task", ui.output_ui("task_form")),

        ui.nav_panel(
            "History",

            # Row for summary cards
            ui.row(
                ui.column(6, ui.output_ui("total_payment_card")),
                ui.column(6, ui.output_ui("total_purchase_card"))
            ),

            # Filter form
            ui.output_ui("filter_form"),

            # History table
            ui.row(
                ui.column(12, ui.output_data_frame("history_table"))),

            # Download button 
            ui.tags.div(
                ui.download_button("download_filtered_history", "Download CSV"),
                style="position: absolute; top: 10px; right: 10px; z-index: 1000;"
            )
        )
    )

app_ui = ui.page_fluid(
    ui.output_ui("main_ui")
)

# --- Server Logic ---
# def server(input, output, session):
def server(input: Inputs, output: Outputs, session: Session):

    user_session = reactive.value(None)

    @output
    @render.ui
    def main_ui():
        """
        This function display the login functionality
        """
        if user_session.get() is None:
            return ui.div(
                ui.TagList(
             
                ui.h2("Login"),
                ui.input_text("login_email", "Username"),
                ui.input_password("login_password", "Password"),
                ui.input_action_button("login_btn", "Log In"),
                ui.output_text("login_message")
                ),
                style="""
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                text-align: center;
            """
            )
    
        else:
            return page_ui()

    @output
    @render.text
    def login_message():
        """
        This function interact with the backend and ensure that users are logged in properly
        with all neccessaries logger
        """

        if input.login_btn() > 0:
            email = input.login_email()
            password = input.login_password().encode('utf-8')
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s", (email,))
                user = cursor.fetchone()
                if user and bcrypt.checkpw(password, user["password_hash"].encode('utf-8')):
                    user_session.set(user)
                    logger.info(f"Login successful for user: {email}")
                    return "Login successful"
                else:
                    logger.warning(f"Login failed for email: {email}")
                    return "Invalid email or password"
            except Exception as e:
                logger.exception(f"Login exception for email: {email}")
                return "An error occurred during login"
            finally:
                cursor.close()
                conn.close()
        return ""

    @output
    @render.text
    def user_authenticated():
        return "true" if user_session.get() is not None else "false"

    @output
    @render.ui
    def task_form():
        user = user_session.get()
        if user:
            logger.debug(f"Rendering task form for: {user['username']}")
        return ui.TagList(
            ui.row(
            ui.column(6, ui.input_radio_buttons("task_type", "Select Task", ["Payment", "Purchase"])),
            ui.column(6, ui.input_select("school_type", "School Type", ["SOML Advanced", "SOML Ordinary", "EFD & Igbaradi"]))),
            ui.output_ui("task_details")
        )
    
    @output
    @render.ui
    def task_details():
        """"""
        task = input.task_type()
        user_email = user_session.get()['username'] if user_session.get() else 'Unknown'
        
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Fetch enrollees
            cursor.execute("SELECT enrollee_id, CONCAT(first_name, ' ', last_name) AS name FROM enrollees")
            enrollee_options = {row["name"]: row["enrollee_id"] for row in cursor.fetchall()}
            enrollee_options["➕ Add new enrollee..."] = "add_new_enrollee"

            # Fetch items
            cursor.execute("SELECT item_id, item_name AS item_name FROM items")
            item_options = {row["item_name"]: row["item_id"] for row in cursor.fetchall()}
            item_options["➕ Add new item..."] = "add_new_item"
            item_options =list(item_options.keys())

            if task == "Payment":
                return ui.TagList(
                    ui.input_select("enrollee", "Select Enrollee", choices=enrollee_options),
                    ui.panel_conditional(
                        "input.enrollee == 'add_new_enrollee'",
                        ui.row(
                            ui.column(6, ui.input_text("first_name", "First Name")),
                            ui.column(6, ui.input_text("last_name", "Last Name"))
                        )
                    ),
                    ui.row(
                        ui.column(6, ui.input_select("fee_type", "Fee Type", ["Registration", "Feeding", "Handout"])),
                        ui.column(6, ui.input_select("month", "Month Paid", [
                            "January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"
                        ]))
                    ),
                    ui.row(
                        ui.column(6, ui.input_numeric("year_paid", "Year Paid", 0)),
                        ui.column(6, ui.input_numeric("amount", "Amount", 0))
                    ),
                    ui.input_action_button("submit_payment", "Submit Payment")
                )

            elif task == "Purchase":
                return ui.TagList(
                    ui.input_select("item", "Select Item", choices=item_options),
                    ui.panel_conditional(
                        "input.item == 'add_new_item'",
                        ui.input_text("new_item_name", "New Item Name")
                    ),
                    ui.row(
                        ui.column(6, ui.input_text("quantity", "Quantity")),
                        ui.column(6, ui.input_numeric("amount", "Amount", 0))
                    ),
                    ui.row(
                        ui.column(6, ui.input_select("month", "Month Paid", [
                            "January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"
                        ])),
                        ui.column(6, ui.input_numeric("year_paid", "Year Paid", 0))
                    ),
                    ui.input_action_button("submit_purchase", "Submit Purchase")
                )

        except Exception as e:
            logger.exception("Error in task_details rendering")
            return ui.div("Error loading form. Please check logs.")
        
        finally:
            cursor.close()
            conn.close()

    @output
    @render.ui
    def filter_form():
     

        return ui.TagList(
        ui.row(
        ui.column(3, ui.input_date_range("filter_date", "Select Date Range")),
        ui.column(3, ui.input_select("filter_school", "Select School", ["All", "SOML Advanced", "SOML Ordinary", "EFD & Igbaradi"])),
        ui.column(3, ui.input_select("filter_type", "Type", ["All", "Payment", "Purchase"])),
        ui.column(3, ui.input_select("filter_fee_type", "Fee Type", choices=["All", "Registration", "Feeding", "Handout"])),
        #ui.column(2, ui.input_select("filter_period", "Filter by Period", choices=["All"]))  # dynamically updated

        ))

    @reactive.Effect
    def update_enrollees():
        school = input.school_type()
        try:
            if school:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT enrollee_id, CONCAT(first_name, ' ', last_name) as name
                    FROM enrollees
                    WHERE school_name = %s
                """, (school,))
                results = cursor.fetchall()
                enrollee_choices = [row[1] for row in results]
                ui.update_select("enrollee", choices=enrollee_choices)
                logger.info(f"Updated enrollee list for school: {school}")
        except Exception as e:
            logger.exception(f"Error updating enrollees for school: {school}")
        finally:
            cursor.close()
            conn.close()

    purchase_pending = reactive.value(False)
    payment_pending = reactive.value(False)


    @reactive.Effect
    def update_items():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT item_name FROM items")
            results = cursor.fetchall()
            item_choices = [row[0] for row in results]
            ui.update_select("item", choices=item_choices)
            logger.info("Updated item list")
        except Exception as e:
            logger.exception("Error updating items")
        finally:
            cursor.close()
            conn.close()

        payment_pending = reactive.value(False)
        payment_submit_count = reactive.value(0)
         
        @reactive.Effect
        def process_payment():
            req(input.submit_payment())

            if input.submit_payment() > payment_submit_count.get() and not payment_pending():
                payment_pending.set(True)
                payment_submit_count.set(input.submit_payment())
                ui.modal_show(show_confirmation_dialog("payment"))

            if input.confirm_payment() > 0 and payment_pending():
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT enrollee_id FROM enrollees WHERE CONCAT(first_name, ' ', last_name) = %s AND school_name = %s", 
                                (input.enrollee(), input.school_type()))
                    enrollee_id = cursor.fetchone()
                    cursor.execute("SELECT school_id FROM school_types WHERE school_name = %s", (input.school_type(),))
                    school_id = cursor.fetchone()

                    if enrollee_id and school_id:
                        cursor.execute("""
                            INSERT INTO payments (enrollee_id, fee_type, amount, month_paid, year_paid, school_id, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """, (enrollee_id[0], input.fee_type(), input.amount(), input.month(), input.year_paid(), school_id[0]))
                        conn.commit()
                        ui.notification_show("Payment successfully recorded!", type="success")
                    else:
                        logger.error("Invalid enrollee or school name.")
                except Exception as e:
                    logger.exception("Error processing payment")
                finally:
                    cursor.close()
                    conn.close()
                    ui.modal_remove()
                    payment_pending.set(False)

            if input.cancel_payment() > 0 and payment_pending():
                payment_pending.set(False)
                print(f"Before Cancel - payment_submit_count: {payment_submit_count.get()}")
                payment_submit_count.set(input.submit_payment() - 1)
                print(f"After Cancel - payment_submit_count: {payment_submit_count.get()}")
                #payment_submit_count.set(-1)

                ui.modal_remove()



    purchase_pending = reactive.value(False)
    purchase_submit_count = reactive.value(0)
    @reactive.Effect
    def process_purchase():
        req(input.submit_purchase())

        # Detect a new submit (only when button clicked newly)
        if input.submit_purchase() > purchase_submit_count.get() and not purchase_pending():
            purchase_pending.set(True)
            purchase_submit_count.set(input.submit_purchase())  # Update count
            ui.modal_show(show_confirmation_dialog("purchase"))

        # Confirm purchase
        if input.confirm_purchase() > 0 and purchase_pending():
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO purchases (item_id, quantity, amount, school_id, month_paid, year_paid, created_at)
                    VALUES (
                        (SELECT item_id FROM items WHERE item_name = %s), %s, %s,
                        (SELECT school_id FROM school_types WHERE school_name = %s), %s, %s,
                        NOW()
                    )
                """, (input.item(), input.quantity(), input.amount(), input.school_type(),
                    input.month(), input.year_paid()))
                conn.commit()
                ui.notification_show("Purchased Item successfully recorded!", type="success")
            except Exception as e:
                logger.exception("Error processing purchase")
            finally:
                cursor.close()
                conn.close()
                ui.modal_remove()
                purchase_pending.set(False)

        # Cancel purchase
        if input.cancel_purchase() > 0 and purchase_pending():
            purchase_pending.set(False)
            purchase_submit_count.set(-1)

            ui.modal_remove()

    def show_confirmation_dialog(action):
        return ui.modal(
            f"Are you sure you want to submit this {action}?",
            title="Confirm Submission",
            easy_close=False,
            footer=ui.TagList(
                ui.input_action_button(f"confirm_{action}", "Yes, Confirm"),
                ui.modal_button("Cancel")
            )
        )
    
    @reactive.calc
    def filtered_history_df():
        """"""
        try:
            logger.info("Rendering history table")
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT 'Payment' as Type, CONCAT(first_name, ' ', last_name) AS Name, amount AS Amount, fee_type AS Category, CONCAT(month_paid, ' ', year_paid) AS Period, created_at, school_id FROM payments p
                JOIN enrollees e ON p.enrollee_id = e.enrollee_id
                UNION ALL
                SELECT 'Purchase' as Type, item_name AS Item, amount AS Amount, quantity AS Quantity, CONCAT(month_paid, ' ', year_paid) AS Period, created_at, school_id FROM purchases pu
                JOIN items e ON pu.item_id = e.item_id
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [i[0] for i in cursor.description]
            df = pd.DataFrame(rows, columns=column_names)

            if input.filter_date():
                start_date, end_date = input.filter_date()
                end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)  # inclusive end
                df['created_at'] = pd.to_datetime(df['created_at'])
                df = df[(df['created_at'] >= pd.to_datetime(start_date)) & (df['created_at'] <= pd.to_datetime(end_date))]
            
            # Filter by fee_type (for Payment only)
            if input.filter_fee_type() != "All":
                df = df[(df['Type'] == "Payment") & (df['Category'] == input.filter_fee_type())]

            if input.filter_school() != "All":
                cursor.execute("SELECT school_id FROM school_types WHERE school_name = %s", (input.filter_school(),))
                school_id = cursor.fetchone()['school_id']
                df = df[df['school_id'] == school_id]
            
            # if input.filter_period() != "All":
                # st_date, e_date = df['Period'].min(), df['Period'].max() #input.filter_period()
                # e_date = pd.to_datetime(e_date) + pd.Timedelta(days=1) 
                # df = df[(df['Period'] >= pd.to_datetime(st_date)) & (df['Period'] <= pd.to_datetime(e_date))]

                # st_date, e_date = input.filter_period()
                # e_date = pd.to_datetime(e_date) + pd.Timedelta(days=1) 
                # #selected_period = pd.to_datetime(input.filter_period(), format="%B %Y", errors='coerce')
                # df['Period'] = pd.to_datetime(df['Period'], format="%B %Y", errors='coerce')  # First of the month
                # df = df[(df['Period'] >= pd.to_datetime(st_date)) & (df['Period'] <= pd.to_datetime(e_date))]
                

                #df = df[df['Period'] == selected_period]

            if input.filter_type() != "All":
                df = df[df['Type'] == input.filter_type()]
            df = df.sort_values(by="created_at", ascending=False)

            return df.drop(columns=['school_id'])
        except Exception as e:
            logger.exception("Error rendering history table")
            return pd.DataFrame()
        finally:
            cursor.close()
            conn.close()



    @output
    @render.data_frame
    def history_table():
        return filtered_history_df()


    @output
    @render.ui
    def total_payment_card():
        df = filtered_history_df()
        total_payment = df[df['Type'] == 'Payment']['Amount'].sum()
        return ui.card(
            ui.h4("Total Payment Made"),
            ui.h3(f"₦{total_payment:,.2f}", class_="text-success")
        )


    @output
    @render.ui
    def total_purchase_card():
        df = filtered_history_df()
        total_purchase = df[df['Type'] == 'Purchase']['Amount'].sum()
        return ui.card(
            ui.h4("Total Items Purchased Cost"),
            ui.h3(f"₦{total_purchase:,.2f}", class_="text-warning")
        )
    
    @output
    @render.download(filename="Report.csv")
    def download_filtered_history():
        df = filtered_history_df()
        yield df.to_csv(index=False)



app = App(app_ui, server)