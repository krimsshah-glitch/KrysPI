from flask import Flask, render_template, request, redirect, session
import csv
import os
from functools import wraps

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


app = Flask(__name__)
app.secret_key = "kryspi_student_tracker_2026"


# --------------------------------------------------
# FILE PATHS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_FILE = os.path.join(BASE_DIR, "expenses.csv")
BUDGET_FILE = os.path.join(BASE_DIR, "budgets.csv")
SAVINGS_FILE = os.path.join(BASE_DIR, "savings.csv")

STATIC_DIR = os.path.join(BASE_DIR, "static")


# --------------------------------------------------
# CSV SETUP
# --------------------------------------------------

def setup_files():
    """
    Creates the CSV files with the correct headings
    if they do not already exist.
    """

    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "User",
                "Amount",
                "Category",
                "Date",
                "Description"
            ])

    if not os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "User",
                "Budget"
            ])

    if not os.path.exists(SAVINGS_FILE):
        with open(SAVINGS_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "User",
                "Goal",
                "Saved"
            ])


setup_files()


# --------------------------------------------------
# USER LOGIN CHECK
# --------------------------------------------------

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user" not in session:
            return redirect("/")

        return function(*args, **kwargs)

    return wrapper


# --------------------------------------------------
# EXPENSE FUNCTIONS
# --------------------------------------------------

def get_all_expenses():
    expenses = []

    if os.path.exists(CSV_FILE):

        with open(
            CSV_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                expenses.append(row)

    return expenses


def get_user_expenses():
    user = session.get("user")

    if not user:
        return []

    expenses = []

    for expense in get_all_expenses():

        if expense.get("User", "").strip().lower() == user.strip().lower():
            expenses.append(expense)

    return expenses


# --------------------------------------------------
# BUDGET FUNCTIONS
# --------------------------------------------------

def get_budget():
    user = session.get("user")

    if not user:
        return 10000

    if not os.path.exists(BUDGET_FILE):
        return 10000

    with open(
        BUDGET_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            saved_user = row.get("User", "").strip()

            if saved_user.lower() == user.strip().lower():

                try:
                    return float(row.get("Budget", 10000))
                except (ValueError, TypeError):
                    return 10000

    return 10000


def save_budget(amount):
    user = session.get("user")

    rows = []
    found = False

    if os.path.exists(BUDGET_FILE):

        with open(
            BUDGET_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row.get("User", "").strip().lower() == user.strip().lower():

                    row["Budget"] = str(amount)
                    found = True

                rows.append(row)

    if not found:
        rows.append({
            "User": user,
            "Budget": str(amount)
        })

    with open(
        BUDGET_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["User", "Budget"]
        )

        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------
# SAVINGS FUNCTIONS
# --------------------------------------------------

def get_savings():
    user = session.get("user")

    if not user:
        return {
            "goal": 0,
            "saved": 0
        }

    if not os.path.exists(SAVINGS_FILE):
        return {
            "goal": 0,
            "saved": 0
        }

    with open(
        SAVINGS_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            saved_user = row.get("User", "").strip()

            if saved_user.lower() == user.strip().lower():

                try:
                    goal = float(row.get("Goal", 0))
                except (ValueError, TypeError):
                    goal = 0

                try:
                    saved = float(row.get("Saved", 0))
                except (ValueError, TypeError):
                    saved = 0

                return {
                    "goal": goal,
                    "saved": saved
                }

    return {
        "goal": 0,
        "saved": 0
    }


def save_savings(goal, saved):
    user = session.get("user")

    rows = []
    found = False

    if os.path.exists(SAVINGS_FILE):

        with open(
            SAVINGS_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row.get("User", "").strip().lower() == user.strip().lower():

                    row["Goal"] = str(goal)
                    row["Saved"] = str(saved)

                    found = True

                rows.append(row)

    if not found:

        rows.append({
            "User": user,
            "Goal": str(goal),
            "Saved": str(saved)
        })

    with open(
        SAVINGS_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["User", "Goal", "Saved"]
        )

        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def login():

    if "user" in session:
        return redirect("/dashboard")

    return render_template("login.html")


@app.route("/select-user", methods=["POST"])
def select_user():

    name = request.form.get("name", "").strip()

    if name:

        session["user"] = name

        return redirect("/dashboard")

    return redirect("/")


@app.route("/dashboard")
@login_required
def dashboard():

    expenses = get_user_expenses()

    total = 0

    for expense in expenses:

        try:
            total += float(expense["Amount"])

        except (ValueError, TypeError, KeyError):
            pass

    budget = get_budget()

    remaining = budget - total

    if remaining < 0:
        remaining = 0

    if budget > 0:
        progress = (total / budget) * 100
    else:
        progress = 0

    if progress > 100:
        progress = 100

    recent_expenses = expenses[-5:]
    recent_expenses.reverse()

    savings = get_savings()

    savings_goal = savings["goal"]
    saved_amount = savings["saved"]

    savings_remaining = savings_goal - saved_amount

    if savings_remaining < 0:
        savings_remaining = 0

    if savings_goal > 0:
        savings_progress = (saved_amount / savings_goal) * 100
    else:
        savings_progress = 0

    if savings_progress > 100:
        savings_progress = 100

    return render_template(
        "dashboard.html",
        user=session["user"],
        total=total,
        budget=budget,
        remaining=remaining,
        progress=progress,
        recent_expenses=recent_expenses,
        savings_goal=savings_goal,
        saved_amount=saved_amount,
        savings_remaining=savings_remaining,
        savings_progress=savings_progress
    )


# --------------------------------------------------
# ADD EXPENSE
# --------------------------------------------------

@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():

    if request.method == "POST":

        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        if amount and category and date:

            with open(
                CSV_FILE,
                "a",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    session["user"],
                    amount,
                    category,
                    date,
                    description
                ])

        return redirect("/add-expense")

    return render_template(
        "add_expense.html",
        user=session["user"]
    )


# --------------------------------------------------
# EXPENSE HISTORY
# --------------------------------------------------

@app.route("/expense-history")
@login_required
def expense_history():

    expenses = get_user_expenses()

    return render_template(
        "expense_history.html",
        expenses=expenses,
        user=session["user"]
    )


# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------

@app.route("/analytics")
@login_required
def analytics():

    expenses = get_user_expenses()

    if not expenses:

        return render_template(
            "analytics.html",
            user=session["user"],
            total=0,
            transaction_count=0,
            top_category="No data",
            top_category_amount=0,
            category_chart=None,
            date_chart=None
        )

    total = 0

    for expense in expenses:

        try:
            total += float(expense["Amount"])

        except (ValueError, TypeError, KeyError):
            pass

    # ----------------------------------------------
    # CATEGORY TOTALS
    # ----------------------------------------------

    category_totals = {}

    for expense in expenses:

        category = expense.get("Category", "Other")

        try:
            amount = float(expense.get("Amount", 0))

        except (ValueError, TypeError):
            continue

        if category in category_totals:
            category_totals[category] += amount

        else:
            category_totals[category] = amount

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())

    if category_totals:

        top_category = max(
            category_totals,
            key=category_totals.get
        )

        top_category_amount = category_totals[top_category]

    else:

        top_category = "No data"
        top_category_amount = 0

    # ----------------------------------------------
    # CATEGORY CHART
    # ----------------------------------------------

    plt.figure(figsize=(9, 5.5))

    bars = plt.bar(
        categories,
        amounts,
        color=[
            "#6C63FF",
            "#7B73FF",
            "#8B84FF",
            "#5B8DEF",
            "#6DD5FA",
            "#72D6B5"
        ][:len(categories)]
    )

    plt.title(
        "Where Your Money Goes",
        fontsize=18,
        fontweight="bold",
        pad=18
    )

    plt.xlabel(
        "Category",
        fontsize=11
    )

    plt.ylabel(
        "Amount (₹)",
        fontsize=11
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.2
    )

    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    plt.gca().set_facecolor("#FBFBFF")

    for bar, amount in zip(bars, amounts):

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            "₹" + str(round(amount)),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    plt.tight_layout()

    category_chart_path = os.path.join(
        STATIC_DIR,
        "category_chart.png"
    )

    plt.savefig(
        category_chart_path,
        dpi=150,
        facecolor="#FBFBFF"
    )

    plt.close()

    # ----------------------------------------------
    # DATE TOTALS
    # ----------------------------------------------

    date_totals = {}

    for expense in expenses:

        date = expense.get("Date", "")

        try:
            amount = float(expense.get("Amount", 0))

        except (ValueError, TypeError):
            continue

        if date in date_totals:
            date_totals[date] += amount

        else:
            date_totals[date] = amount

    dates = sorted(date_totals.keys())

    date_amounts = [
        date_totals[date]
        for date in dates
    ]

    # ----------------------------------------------
    # DATE CHART
    # ----------------------------------------------

    plt.figure(figsize=(9, 5.5))

    x_values = list(range(len(dates)))

    plt.plot(
        x_values,
        date_amounts,
        marker="o",
        linewidth=3,
        markersize=7,
        color="#6C63FF"
    )

    plt.fill_between(
        x_values,
        date_amounts,
        alpha=0.10,
        color="#6C63FF"
    )

    plt.title(
        "Your Spending Journey",
        fontsize=18,
        fontweight="bold",
        pad=18
    )

    plt.xlabel(
        "Date",
        fontsize=11
    )

    plt.ylabel(
        "Amount (₹)",
        fontsize=11
    )

    plt.xticks(
        x_values,
        dates,
        rotation=45
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.2
    )

    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    plt.gca().set_facecolor("#FBFBFF")

    plt.tight_layout()

    date_chart_path = os.path.join(
        STATIC_DIR,
        "date_chart.png"
    )

    plt.savefig(
        date_chart_path,
        dpi=150,
        facecolor="#FBFBFF"
    )

    plt.close()

    return render_template(
        "analytics.html",
        user=session["user"],
        total=total,
        transaction_count=len(expenses),
        top_category=top_category,
        top_category_amount=top_category_amount,
        category_chart="category_chart.png",
        date_chart="date_chart.png"
    )


# --------------------------------------------------
# BUDGET
# --------------------------------------------------

@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():

    if request.method == "POST":

        try:

            amount = float(
                request.form.get("budget", 0)
            )

            if amount > 0:
                save_budget(amount)

        except (ValueError, TypeError):
            pass

        return redirect("/dashboard")

    return render_template(
        "budget.html",
        user=session["user"],
        budget=get_budget()
    )


# --------------------------------------------------
# SAVINGS
# --------------------------------------------------

@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings():

    if request.method == "POST":

        try:

            goal = float(
                request.form.get("goal", 0)
            )

            saved = float(
                request.form.get("saved", 0)
            )

            if goal < 0:
                goal = 0

            if saved < 0:
                saved = 0

            save_savings(
                goal,
                saved
            )

        except (ValueError, TypeError):
            pass

        return redirect("/savings")

    current_savings = get_savings()

    goal = current_savings["goal"]
    saved = current_savings["saved"]

    remaining = goal - saved

    if remaining < 0:
        remaining = 0

    if goal > 0:
        progress = (saved / goal) * 100
    else:
        progress = 0

    if progress > 100:
        progress = 100

    return render_template(
        "savings.html",
        user=session["user"],
        goal=goal,
        saved=saved,
        remaining=remaining,
        progress=progress
    )


# --------------------------------------------------
# CLEAR CURRENT USER'S RECORDS
# --------------------------------------------------

@app.route("/clear-records", methods=["POST"])
@login_required
def clear_records():

    user = session["user"]

    # ----------------------------------------------
    # CLEAR EXPENSES FOR CURRENT USER ONLY
    # ----------------------------------------------

    rows = []

    if os.path.exists(CSV_FILE):

        with open(
            CSV_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row.get("User", "").strip().lower() != user.strip().lower():
                    rows.append(row)

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "User",
                "Amount",
                "Category",
                "Date",
                "Description"
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    # ----------------------------------------------
    # CLEAR BUDGET FOR CURRENT USER
    # ----------------------------------------------

    budget_rows = []

    if os.path.exists(BUDGET_FILE):

        with open(
            BUDGET_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row.get("User", "").strip().lower() != user.strip().lower():
                    budget_rows.append(row)

    with open(
        BUDGET_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["User", "Budget"]
        )

        writer.writeheader()
        writer.writerows(budget_rows)

    # ----------------------------------------------
    # CLEAR SAVINGS FOR CURRENT USER
    # ----------------------------------------------

    savings_rows = []

    if os.path.exists(SAVINGS_FILE):

        with open(
            SAVINGS_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row.get("User", "").strip().lower() != user.strip().lower():
                    savings_rows.append(row)

    with open(
        SAVINGS_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["User", "Goal", "Saved"]
        )

        writer.writeheader()
        writer.writerows(savings_rows)

    return redirect("/dashboard")


# --------------------------------------------------
# SWITCH USER
# --------------------------------------------------

@app.route("/switch-user")
def switch_user():

    session.clear()

    return redirect("/")


# --------------------------------------------------
# RUN APP
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)