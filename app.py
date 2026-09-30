from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "lab_secret_key"

DB_NAME = "products.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            special TEXT NOT NULL,
            date_added TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def index():
    sort = request.args.get("sort", "id")

    if sort == "special":
        order_by = "special"
    else:
        order_by = "product_id"

    conn = get_db_connection()
    products = conn.execute(
        f"SELECT rowid, * FROM products ORDER BY {order_by}"
    ).fetchall()
    conn.close()

    return render_template("index.html", products=products)


@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        product_id = request.form["product_id"].strip()
        name = request.form["name"].strip()
        price = request.form["price"].strip()
        special = request.form["special"].strip()
        date_added = request.form["date_added"].strip()

        if not product_id or not name or not price or not special or not date_added:
            flash("All fields are required.")
            return render_template(
                "form.html",
                title="Add product",
                product=None,
                today=date.today().isoformat()
            )

        try:
            product_id = int(product_id)
        except ValueError:
            flash("ID must be an integer.")
            return render_template(
                "form.html",
                title="Add product",
                product=None,
                today=date.today().isoformat()
            )

        try:
            price = float(price)

            if price < 0:
                raise ValueError
        except ValueError:
            flash("Price must be a non-negative number.")
            return render_template(
                "form.html",
                title="Add product",
                product=None,
                today=date.today().isoformat()
            )

        conn = get_db_connection()

        existing_product = conn.execute(
            "SELECT * FROM products WHERE product_id = ?",
            (product_id,)
        ).fetchone()

        if existing_product:
            conn.close()
            flash("Product with this ID already exists.")
            return render_template(
                "form.html",
                title="Add product",
                product=None,
                today=date.today().isoformat()
            )

        conn.execute("""
            INSERT INTO products
            (product_id, name, price, special, date_added)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, name, price, special, date_added))

        conn.commit()
        conn.close()

        flash("Product added successfully.")
        return redirect(url_for("index"))

    return render_template(
        "form.html",
        title="Add product",
        product=None,
        today=date.today().isoformat()
    )


@app.route("/edit/<int:row_id>", methods=["GET", "POST"])
def edit_product(row_id):
    conn = get_db_connection()

    product = conn.execute(
        "SELECT rowid, * FROM products WHERE rowid = ?",
        (row_id,)
    ).fetchone()

    if product is None:
        conn.close()
        return "Product not found", 404

    if request.method == "POST":
        product_id = request.form["product_id"].strip()
        name = request.form["name"].strip()
        price = request.form["price"].strip()
        special = request.form["special"].strip()
        date_added = request.form["date_added"].strip()

        if not product_id or not name or not price or not special or not date_added:
            conn.close()
            flash("All fields are required.")
            return render_template(
                "form.html",
                title="Edit product",
                product=product,
                today=date.today().isoformat()
            )

        try:
            product_id = int(product_id)
        except ValueError:
            conn.close()
            flash("ID must be an integer.")
            return render_template(
                "form.html",
                title="Edit product",
                product=product,
                today=date.today().isoformat()
            )

        try:
            price = float(price)

            if price < 0:
                raise ValueError
        except ValueError:
            conn.close()
            flash("Price must be a non-negative number.")
            return render_template(
                "form.html",
                title="Edit product",
                product=product,
                today=date.today().isoformat()
            )

        # BUG:
        # Here we do not check whether another product
        # already has the same product_id.

        conn.execute("""
            UPDATE products
            SET product_id = ?,
                name = ?,
                price = ?,
                special = ?,
                date_added = ?
            WHERE rowid = ?
        """, (
            product_id,
            name,
            price,
            special,
            date_added,
            row_id
        ))

        conn.commit()
        conn.close()

        flash("Product updated successfully.")
        return redirect(url_for("index"))

    conn.close()

    return render_template(
        "form.html",
        title="Edit product",
        product=product,
        today=date.today().isoformat()
    )


@app.route("/delete/<int:row_id>", methods=["POST"])
def delete_product(row_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM products WHERE rowid = ?",
        (row_id,)
    )

    conn.commit()
    conn.close()

    flash("Product deleted successfully.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
