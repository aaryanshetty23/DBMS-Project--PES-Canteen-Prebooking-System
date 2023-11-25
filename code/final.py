import streamlit as st
import mysql.connector
from mysql.connector import Error
def connect_to_database():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="aaryan",
            database="pesu_canteen"
        )
        return db
    except Error as e:
        st.error(f"Error: {e}")
        return None

def signup_user(name, phone, email, password):
    try:
        db = connect_to_database()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM customer")
        user_count = cursor.fetchone()[0] + 2
        user_id = f"U_{user_count}"
        query = "INSERT INTO customer (user_id, phone, name, email, password) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (user_id, phone, name, email, password))
        db.commit()

        st.success("User signed up successfully!")
        st.info(f"Your user_id: {user_id}")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()

# Function to authenticate user
def authenticate_user(email, password):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        
        query = "SELECT * FROM customer WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            return user, "customer"

        
        query = "SELECT * FROM canteen WHERE canteen_id = %s AND password = %s"
        cursor.execute(query, (email, password))
        canteen_owner = cursor.fetchone()

        if canteen_owner:
            return canteen_owner, "canteen_owner"

        return None, None

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()


def get_canteens():
    try:
        db = connect_to_database()
        cursor = db.cursor()

        query = "SELECT * FROM canteen"
        cursor.execute(query)
        canteens = cursor.fetchall()

        return canteens
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()


def get_menu_items(canteen_id):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        query = "SELECT * FROM menu_items WHERE canteen_id = %s"
        

        cursor.execute(query, (canteen_id,))
        menu_items = cursor.fetchall()

        return menu_items
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()

# Function to calculate total price for an order using stored function
def calculate_total_price(order_id):  #--------------------------function------------
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Call the stored function
        calculate_total_price_function = "SELECT CalculateTotalPrice(%s)"
        cursor.execute(calculate_total_price_function, (order_id,))
        total_price = cursor.fetchone()[0]

        return total_price

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()

# Function to place an order
def place_order(user_id, canteen_id, items):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Check if there is an existing order for the user and canteen
        existing_order_query = "SELECT order_id FROM `order` WHERE user_id = %s AND canteen_id = %s AND status = 'Placed'"
        cursor.execute(existing_order_query, (user_id, canteen_id))
        existing_order = cursor.fetchone()

        if existing_order:
            # If there is an existing order, update it
            order_id = existing_order[0]
            total_price_query = "SELECT total_price FROM `order` WHERE order_id = %s"
            cursor.execute(total_price_query, (order_id,))
            current_total_price = cursor.fetchone()[0]

            for item_id, quantity in items.items():
                menu_item_query = "SELECT * FROM menu_items WHERE menuitem_id = %s"
                cursor.execute(menu_item_query, (item_id,))
                menu_item = cursor.fetchone()
                subtotal = quantity * menu_item[4]
                current_total_price += subtotal

            # Update total price in the order table
            update_total_price_query = "UPDATE `order` SET total_price = %s WHERE order_id = %s"
            cursor.execute(update_total_price_query, (current_total_price, order_id))

            # Insert order items into the database
            for item_id, quantity in items.items():
                order_item_id = f"OI_{order_id}_{item_id}"
                menu_item_query = "SELECT * FROM menu_items WHERE menuitem_id = %s"
                cursor.execute(menu_item_query, (item_id,))
                menu_item = cursor.fetchone()
                subtotal = quantity * menu_item[4]

                # Inserting data into order_items table with canteen_id and user_id
                order_item_query = "INSERT INTO order_items (orderitem_id, order_id, menuitem_id, quantity, subtotal, canteen_id, user_id) " \
                                   "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(order_item_query, (order_item_id, order_id, item_id, quantity, subtotal, canteen_id, user_id))

            db.commit()
        else:
            # If there is no existing order, create a new one
            # Generate order_id
            cursor.execute("SELECT COUNT(*) FROM `order`")
            order_count = cursor.fetchone()[0] + 1
            order_id = f"O_{order_count}"
            
            # Insert order into the database
           
            order_query = "INSERT INTO `order` (order_id, user_id, date, total_price, status, canteen_id) " \
                          "VALUES (%s, %s, CURDATE(), 0, 'Placed', %s)"
            cursor.execute(order_query, (order_id, user_id, canteen_id))

            # Insert order items into the database
            for item_id, quantity in items.items():
                order_item_id = f"OI_{order_id}_{item_id}"
                menu_item_query = "SELECT * FROM menu_items WHERE menuitem_id = %s"
                cursor.execute(menu_item_query, (item_id,))
                menu_item = cursor.fetchone()
                subtotal = quantity * menu_item[4]

                # Inserting data into order_items table with canteen_id and user_id
                order_item_query = "INSERT INTO order_items (orderitem_id, order_id, menuitem_id, quantity, subtotal, canteen_id, user_id) " \
                                   "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(order_item_query, (order_item_id, order_id, item_id, quantity, subtotal, canteen_id, user_id))

            db.commit()
            st.success("Order placed successfully!")

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()

# Function to confirm an order using stored procedure and function
def confirm_order(user_id, user_type):        #------------------------stored procedure and join-----------------
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Get all order_items for the user
        get_user_orders_query = """
        SELECT OI.orderitem_id, OI.menuitem_id, MI.item_name, MI.price, OI.quantity, OI.subtotal, OI.canteen_id
        FROM order_items OI
        INNER JOIN menu_items MI ON OI.menuitem_id = MI.menuitem_id
        WHERE OI.user_id = %s
        """
        cursor.execute(get_user_orders_query, (user_id,))
        user_orders = cursor.fetchall()

        # Display order_items
        st.subheader("Your Orders:")
        for order_item in user_orders:
            st.write(f"{order_item[2]} - Quantity: {order_item[4]}, Subtotal: ₹{order_item[5]:.2f}")

        # Confirm Order button
        if st.button("Confirm Order"):
            # Extract the order_id from the orderitem_id
            order_id = order_item[0].split('_')[2]  # Assuming the order_id is the third part of the orderitem_id

            if user_type == "customer":
                # Call the stored procedure for customers
                cursor.callproc("ConfirmOrder", (user_id,))
            else:
                # Display message for canteen owners
                st.warning("Log in as a customer to confirm an order.")

            # Fetch the result (if needed)
            result = cursor.fetchone()

            # Commit the changes
            db.commit()

            st.success("Order confirmed successfully!")

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()

# Function to view current orders for canteen owners
def view_current_orders(canteen_id): #---------------nested-----------------
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Get all order_items for the canteen
        get_canteen_orders_query = """
        SELECT OI.orderitem_id, OI.menuitem_id, MI.item_name, MI.price, OI.quantity, OI.subtotal, OI.user_id
        FROM order_items OI
        INNER JOIN menu_items MI ON OI.menuitem_id = MI.menuitem_id
        WHERE OI.canteen_id = %s AND OI.order_id IN (
            SELECT order_id
            FROM `order`
            WHERE status = 'Confirmed'
        )
        """
        cursor.execute(get_canteen_orders_query, (canteen_id,))
        canteen_orders = cursor.fetchall()
        

        # Display canteen orders
        st.subheader("Current Orders:")
        for order_item in canteen_orders:
            st.write(f"{order_item[2]} - Quantity: {order_item[4]}, Subtotal: ₹{order_item[5]:.2f}, User: {order_item[6]}")

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()
# Function to add a menu item for canteen owners
def add_menu_item(canteen_id, item_name, item_description, item_price):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Calculate the new menu item ID
        cursor.execute("SELECT COUNT(*) FROM menu_items")
        menu_item_count = cursor.fetchone()[0] + 1
        menu_item_id = f"M_{menu_item_count}"

        # Insert the new menu item into the database
        query = "INSERT INTO menu_items (menuitem_id, canteen_id, item_name, item_description, price) " \
                "VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (menu_item_id, canteen_id, item_name, item_description, item_price))
        db.commit()

        st.success("Menu item added successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()
    
# Function to get total sales by canteen for a specific canteen owner-------------- aggregate query
def get_total_sales_by_canteen(canteen_id):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Display total sales for the canteen owner's canteen
        get_total_sales_query = """
        SELECT O.canteen_id, C.canteen_name, SUM(O.total_price) AS total_sales
        FROM `order` O
        INNER JOIN canteen C ON O.canteen_id = C.canteen_id
        WHERE O.canteen_id = %s
        GROUP BY O.canteen_id, C.canteen_name
        """
        cursor.execute(get_total_sales_query, (canteen_id,))
        total_sales = cursor.fetchall()

        return total_sales

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()

# Function to delete a user
def delete_user(user_id, user_type):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        if user_type == "customer":
            # Delete the user from the customer table
            delete_user_query = "DELETE FROM customer WHERE user_id = %s"
        elif user_type == "canteen_owner":
            # Delete the user from the canteen table
            delete_user_query = "DELETE FROM canteen WHERE canteen_id = %s"
        else:
            st.error("Invalid user type")
            return

        cursor.execute(delete_user_query, (user_id,))
        db.commit()

        st.success("User deleted successfully!")

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()



# Streamlit UI
def main():
    
    st.title("PESU CANTEEN PREBOOKING MANAGEMENT")

    # Login and Signup Section
    st.session_state.user_id = st.session_state.get("user_id", None)
    st.session_state.user_type = st.session_state.get("user_type", None)

    st.sidebar.title("Menu")

    # Display only relevant options based on user type
    if st.session_state.user_type == "customer":
        menu_option = st.sidebar.radio("Choose an option", ["Login", "Signup","Place Order", "Confirm Order", "Delete User"])
    elif st.session_state.user_type == "canteen_owner":
        menu_option = st.sidebar.radio("Choose an option", ["Login", "Signup","View Current Orders", "Add Menu Item","View Total Sales", "Delete User"])
    else:
        menu_option = st.sidebar.radio("Choose an option", ["Login", "Signup", "Delete User"])

    if menu_option == "Login":
        st.header("Login")
        login_option = st.radio("Login as", ["Customer", "Canteen Owner"])
        email = st.text_input("User login ID")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user, user_type = authenticate_user(email, password)

            if user_type == "customer" and login_option == "Customer":
                st.session_state.user_id = user[0]
                st.session_state.user_type = "customer"
                st.sidebar.success(f"Logged in as {user[2]}")
            elif user_type == "canteen_owner" and login_option == "Canteen Owner":
                st.session_state.user_id = user[0]
                st.session_state.user_type = "canteen_owner"
                st.sidebar.success(f"Logged in as {user[1]} (Canteen Owner)")
            else:
                st.sidebar.error("Authentication Failed. Please check your credentials.")

    elif menu_option == "Signup":
        st.header("Signup")
        name = st.text_input("Full Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Signup"):
            signup_user(name, phone, email, password)
    
    elif menu_option == "Delete User":
        st.header("Delete User")
        if st.button("Delete User"):
            delete_user(st.session_state.user_id, st.session_state.user_type)
            st.session_state.user_id = None
            st.session_state.user_type = None
        

    # Conditionally show/hide sections based on user type
    elif menu_option == "Place Order" and st.session_state.user_type == "customer":
        st.header("Place Order")

        # Get canteens
        canteens = get_canteens()
        canteen_names = [canteen[1] for canteen in canteens]
        selected_canteen_name = st.selectbox("Select Canteen", canteen_names, key="selected_canteen")

        # Get menu items for the selected canteen
        selected_canteen_id = next(canteen[0] for canteen in canteens if canteen[1] == selected_canteen_name)
        menu_items = get_menu_items(selected_canteen_id)

        # Display menu items
        st.subheader("Menu Items:")
        for item in menu_items:
            st.write(f"{item[2]} - Price: ₹{item[4]:.2f}")

        # Order form
        st.subheader("Place Your Order:")
        items = {}
        for item in menu_items:
            quantity = st.number_input(f"Quantity of {item[2]}", min_value=0, key=f"quantity_{item[0]}")
            if quantity > 0:
                items[item[0]] = quantity

        if st.button("Place Order"):
            place_order(st.session_state.user_id, selected_canteen_id, items)

    elif menu_option == "Confirm Order" and st.session_state.user_type == "customer":
        st.header("Confirm Order")
        confirm_order(st.session_state.user_id, st.session_state.user_type)

    elif menu_option == "View Current Orders" and st.session_state.user_type == "canteen_owner":
        st.header("View Current Orders")
        view_current_orders(st.session_state.user_id)
    
    elif menu_option == "Add Menu Item" and st.session_state.user_type == "canteen_owner":
        st.header("Add Menu Item")

        # Get canteen ID for the canteen owner
        canteen_id = st.session_state.user_id

        # Input fields for the new menu item
        item_name = st.text_input("Item Name")
        item_description = st.text_area("Item Description")
        item_price = st.number_input("Item Price", min_value=0.0)

        if st.button("Add Menu Item"):
            add_menu_item(canteen_id, item_name, item_description, item_price)
    elif menu_option == "View Total Sales" and st.session_state.user_type == "canteen_owner":
        st.header("View Total Sales")

        # Call the function to get total sales by canteen for the logged-in canteen owner
        total_sales = get_total_sales_by_canteen(st.session_state.user_id)

        st.subheader("Total Sales for Your Canteen:")
        for sale in total_sales:
            st.write(f"Canteen ID: {sale[0]}, Canteen Name: {sale[1]}, Total Sales: ₹{sale[2]:.2f}")
    else:
        st.warning("Select a valid option or log in with the correct user type.")

if __name__ == "__main__":
    main()