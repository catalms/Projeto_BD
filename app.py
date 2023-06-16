#!/usr/bin/python3
from logging.config import dictConfig

import psycopg
from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool


# postgres://{user}:{password}@{hostname}:{port}/{database-name}
DATABASE_URL = "postgres://db:db@postgres/db"

pool = ConnectionPool(conninfo=DATABASE_URL)
# the pool starts connecting immediately.

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)
log = app.logger


@app.route("/accounts", methods=("GET",))
def account_index():
    """Show all the accounts, most recent first."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            accounts = cur.execute(
                """
                SELECT account_number, branch_name, balance
                FROM account
                ORDER BY account_number ASC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(accounts)
    #return jsonify(accounts)
    return render_template("account/index.html", accounts=accounts)


@app.route("/accounts/<account_number>/update", methods=("GET", "POST"))
def account_update(account_number):
    """Update the account balance."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            account = cur.execute(
                """
                SELECT account_number, branch_name, balance
                FROM account
                WHERE account_number = %(account_number)s;
                """,
                {"account_number": account_number},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    if request.method == "POST":
        balance = request.form["balance"]

        error = None

        if not balance:
            error = "Balance is required."
            if not balance.isnumeric():
                error = "Balance is required to be numeric."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        UPDATE account
                        SET balance = %(balance)s
                        WHERE account_number = %(account_number)s;
                        """,
                        {"account_number": account_number, "balance": balance},
                    )
                conn.commit()
            return redirect(url_for("account_index"))

    return render_template("account/update.html", account=account)


@app.route("/accounts/<account_number>/delete", methods=("POST",))
def account_delete(account_number):
    """Delete the account."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """ 
                DELETE FROM account
                WHERE account_number = %(account_number)s;
                """,
                {"account_number": account_number},
            )
        conn.commit()
    return redirect(url_for("account_index"))



""" PRODUCT ROUTES """

@app.route("/", methods=("GET",))
@app.route("/products", methods=("GET",))
def products_index():
    """Show all the accounts, most recent first."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            products = cur.execute(
                """
                SELECT name, SKU, description, price
                FROM product
                ORDER BY name ASC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(products)
    # return jsonify(products)
    return render_template("products/index.html", products=products)

@app.route("/products/register", methods=("POST", "GET"))
def product_register():
    """Register a new product."""

    if request.method == "POST":
        name = request.form["name"]
        sku = request.form["sku"]
        ean = request.form["ean"]
        description = request.form["description"]
        price = request.form["price"]

        error = None

        if not name:
            error = "Name is required."
        elif not sku:
            error = "SKU is required."
        elif not description:
            error = "Description is required."
        elif not price:
            error = "Price is required."
            if not price.isnumeric():
                error = "Price is required to be numeric."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        INSERT INTO product (SKU, name, description, price, ean)
                        VALUES (%(sku)s, %(name)s, %(description)s, %(price)s, %(ean)s);
                        """,
                        {"sku":sku, "name": name, "description": description, "price": price, "ean": ean},
                    )
                conn.commit()
            return redirect(url_for("products_index"))

    return render_template("products/register.html")

@app.route("/products/<product_sku>/update", methods=("GET", "POST"))
def product_update(product_sku):
    """Update product description and price"""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            product = cur.execute(
                """
                SELECT price, description
                FROM product
                WHERE sku = %(product_sku)s;
                """,
                {"product_sku": product_sku},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    if request.method == "POST":
        price = request.form["price"]
        description = request.form["description"]

        error = None

        if not price:
            error = "Balance is required."
            if not price.isnumeric():
                error = "Balance is required to be numeric."
        elif not description:
            error = "Description is required."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        UPDATE product
                        SET price = %(price)s, description = %(description)s
                        WHERE product_sku = %(product_sku)s;
                        """,
                        {"product_sku": product_sku, "price": price, "description": description},
                    )
                conn.commit()
            return redirect(url_for("product_index"))

    return render_template("products/update.html", product=product)

@app.route("/<cust_no>/<order_no>/shop", methods=("GET",))
def shopping(cust_no, order_no):
    """Show all the products, most recent first."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            products = cur.execute(
                """
                SELECT name, SKU, description, price
                FROM product
                ORDER BY name ASC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(products)
    # return jsonify(products)
    return render_template("products/index_customer.html", products=products, order_no=order_no, cust_no=cust_no)



""" CUSTOMER ROUTES """

@app.route("/customers", methods=("GET",))
def customers_index():
    """Show all the accounts, most recent first."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            customers = cur.execute(
                """
                SELECT cust_no, name, email, phone, address
                FROM customer;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(customers)
    # return jsonify(customers)
    return render_template("customer/index.html", customers=customers)


@app.route("/customers/register", methods=("POST", "GET"))
def customer_register():
    """Register a new customer."""

    if request.method == "POST":
        # cust_no = request.form["cust_no"]
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]

        error = None

        # if not cust_no:
        #     error = "Customer number is required."
        if not name:
            error = "Name is required."
        elif not email:
            error = "Email is required."
        elif not phone:
            error = "Phone number is required."
        elif not address:
            error = "Address is required."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cust_no = cur.execute(
                        """
                        SELECT MAX(cust_no) 
                        FROM customer
                        """
                    ).fetchone()

                    cust_no = cust_no[0] + 1

                    cur.execute(
                        """
                        INSERT INTO customer (cust_no, name, email, phone, address)
                        VALUES (%(cust_no)s, %(name)s, %(email)s, %(phone)s, %(address)s);
                        """,
                        {"cust_no":cust_no, "name": name, "email": email, "phone": phone, "address": address},
                    )
            
            conn.commit()
            return redirect(url_for("customers_index"))

    return render_template("customer/register.html")

@app.route("/customers/<cust_no>/delete", methods=("GET", "POST"))
def customer_delete(cust_no):
    """Delete the customer."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """ 
                DELETE FROM customer
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            )
        conn.commit()
    return redirect(url_for("customer_index"))


""" SUPPLIER ROUTES """
@app.route("/suppliers", methods=("GET",))
def suppliers_index():
    """Show all the suppliers, most recent first."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            suppliers = cur.execute(
                """
                SELECT TIN, name, address, SKU, date
                FROM supplier;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")
        
    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(suppliers)
    # return jsonify(customers)
    return render_template("suppliers/index.html", suppliers=suppliers)
    
@app.route("/suppliers/register", methods=("POST", "GET"))
def supplier_register():
    """Register a new supplier."""

    if request.method == "POST":
        tin = request.form["tin"]
        name = request.form["name"]
        address = request.form["address"]
        sku = request.form["sku"]
        date = date.today()

        error = None

        if not tin:
            error = "TIN is required."
        elif not name:
            error = "Name is required."
        elif not address:
            error = "Address is required."
        elif not sku:
            error = "SKU is required."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        INSERT INTO supplier (TIN, name, address, SKU, date)
                        VALUES (%(tin)s, %(name)s, %(address)s, %(sku)s, %(date)s);
                        """,
                        {"tin":tin, "name": name, "address": address, "sku": sku, "date": date},
                    )
                conn.commit()
            return redirect(url_for("suppliers_index"))

    return render_template("suppliers/register.html")   

""" ORDER ROUTES """

@app.route("/order_customer", methods=("GET", "POST"))
def set_customer():
    if request.method == "POST":
        cust_name = request.form["name"]

        error = None

        if not cust_name:
            error = "Customer name is required."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    order_no = cur.execute(
                        """
                        SELECT MAX(order_no)
                        FROM orders;
                        """
                    ).fetchone()

                    order_no = order_no[0] + 1

                    cust_no = cur.execute(
                        """
                        SELECT cust_no
                        FROM customer
                        WHERE name = %(cust_name)s;
                        """,
                        {"cust_name": cust_name}
                    ).fetchone()

                    cur.execute(
                        """
                        INSERT INTO orders
                        values (%(order_no)s, %(cust_no)s, CURRENT_DATE);
                        """,
                        {"order_no": order_no, "cust_no": cust_no[0]}
                    )
                conn.commit()
            
            return redirect(url_for('shopping', order_no=order_no, cust_no=cust_no[0]))
    return render_template("order/set_customer.html")

@app.route("/order", methods=("GET", "POST"))
def create_order():
    if request.method == "POST":
        # order_no = request.form["order_no"]
        cust_no = request.form["cust_no"]
        date = date.today()

        sku_1 = request.form["product_1"]
        qty_1 = request.form["qty_1"]
        
        error = None

        # if not order_no:
        #     error = "Order number is required."
        if not cust_no:
            error = "Customer number is required."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    order_no = cur.execute(
                        """
                        SELECT MAX(order_no)
                        FROM orders;
                        """
                    ).fetchone()

                    order_no = order_no[0] + 1

                    cur.execute("BEGIN;")
                    cur.execute(
                        """
                        INSERT INTO orders (order_no, cust_no, date)
                        VALUES (%(order_no)s, %(cust_no)s, %(date)s);
                        """,
                        {"order_no":order_no, "cust_no": cust_no, "date": date},
                    )

                    cur.execute(
                        """
                        INSERT INTO contains (order_no, SKU, quantity)
                        VALUES (%(order_no)s, %(sku_1)s, 1);
                        ON CONFLICT (order_no, SKU) DO UPDATE
                        SET quantity = contains.quantity + 1; 
                        """,
                        {"order_no":order_no, "SKU":sku_1, "quantity": qty_1},
                    )
                conn.commit()

            return redirect(url_for("order"))
    return render_template("order/create.html")

@app.route("/<cust_no>/<order_no>/<product_sku>", methods=( "POST",))
def add_to_cart(product_sku, order_no, cust_no):
    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                INSERT INTO contains (order_no, SKU, qty)
                VALUES (%(order_no)s, %(product_sku)s, 1)
                ON CONFLICT (order_no, SKU) DO UPDATE
                SET qty = contains.qty + 1; 
                """,
                {"order_no": order_no, "product_sku": product_sku},
            )
        conn.commit()
    return redirect(url_for("shopping", order_no=order_no, cust_no=cust_no))

@app.route("/<cust_no>/<order_no>/checkout", methods=("GET", "POST"))
def checkout(cust_no, order_no):
    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:

            products = cur.execute(
                """
                SELECT p.name, p.description, p.price, c.qty, SUM(p.price * c.qty) AS subtotal
                FROM contains c
                NATURAL JOIN product p
                WHERE c.order_no = %(order_no)s
                GROUP BY p.name, qty, price, p.description;
                """,
                {"order_no": order_no}
            ).fetchall()

            total = cur.execute(
                """
                SELECT SUM(p.price * c.qty) AS total
                FROM contains c
                NATURAL JOIN product p
                WHERE c.order_no = %(order_no)s;
                """,
                {"order_no": order_no}
            ).fetchone()

            conn.commit()
    
    return render_template("order/checkout.html", products=products, total=total, cust_no=cust_no, order_no=order_no)

@app.route("/<cust_no>/<order_no>/payed", methods=("GET", "POST"))
def confirm_payment(cust_no, order_no):
    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                INSERT INTO pay
                values (%(cust_no)s, %(order_no)s);
                """,
                {"cust_no": cust_no, "order_no": order_no}
            )
            conn.commit()

    return redirect(url_for("set_customer"))

@app.route("/ping", methods=("GET",))
def ping():
    log.debug("ping!")
    return jsonify({"message": "pong!", "status": "success"})


if __name__ == "__main__":
    app.run()
