from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file
)

import pandas as pd
import os
import plotly.express as px
import json
import math
import plotly.graph_objects as go
import plotly.io as pio
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from flask import render_template, redirect, url_for, session
import numpy as np

app = Flask(__name__)

app.secret_key = "enterprise_hr_secret_key"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global DataFrame
df = None


# ==========================================================
# LOGIN PAGE
# ==========================================================

@app.route("/")
def login_page():

    return render_template("login.html")


# ==========================================================
# LOGIN VALIDATION
# ==========================================================

@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "admin123":

        session["user"] = username

        return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        error="Invalid Username or Password"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login_page"))


# ==========================================================
# DASHBOARD
# ==========================================================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login_page"))

    return render_template("dashboard.html")


# ==========================================================
# UPLOAD PAGE
# ==========================================================

@app.route("/upload")
def upload():

    if "user" not in session:
        return redirect(url_for("login_page"))

    return render_template("upload.html") 
# ==========================================================
# UPLOAD DATASET
# ==========================================================

@app.route("/upload_file", methods=["POST"])
def upload_file():

    global df

    if "user" not in session:
        return redirect(url_for("login_page"))

    if "file" not in request.files:
        return "Please select a CSV file."

    file = request.files["file"]

    if file.filename == "":
        return "Please choose a CSV file."

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    df = pd.read_csv(filepath)

    rows = df.shape[0]
    columns = df.shape[1]

    column_names = list(df.columns)

    table = df.head(10).to_html(
        classes="table table-striped table-bordered",
        index=False
    )

    total_employees = len(df)

    average_age = 0
    if "Age" in df.columns:
        average_age = round(df["Age"].mean(), 2)

    departments = 0
    if "Department" in df.columns:
        departments = df["Department"].nunique()

    attrition = 0
    if "Attrition" in df.columns:
        attrition = len(df[df["Attrition"] == "Yes"])

    department_chart = None

    if "Department" in df.columns:

        dept = df["Department"].value_counts().reset_index()
        dept.columns = ["Department", "Employees"]

        fig = px.bar(
            dept,
            x="Department",
            y="Employees",
            title="Department Distribution"
        )

        department_chart = fig.to_html(full_html=False)

    attrition_chart = None

    if "Attrition" in df.columns:

        fig = px.pie(
            df,
            names="Attrition",
            title="Employee Attrition"
        )

        attrition_chart = fig.to_html(full_html=False)

    return render_template(

        "preview.html",

        filename=file.filename,

        rows=rows,

        columns=columns,

        table=table,

        column_names=column_names,

        total_employees=total_employees,

        average_age=average_age,

        departments=departments,

        attrition=attrition,

        department_chart=department_chart,

        attrition_chart=attrition_chart

    )
# ==========================================================
# ANALYTICS PAGE
# ==========================================================

@app.route("/analytics")
def analytics():

    global df

    if "user" not in session:
        return redirect(url_for("login_page"))

    if df is None:
        return redirect(url_for("upload"))

    total = len(df)

    avg_age = 0
    if "Age" in df.columns:
        avg_age = round(df["Age"].mean(), 2)

    avg_income = 0
    if "MonthlyIncome" in df.columns:
        avg_income = round(df["MonthlyIncome"].mean(), 2)

    male = 0
    female = 0

    if "Gender" in df.columns:
        male = len(df[df["Gender"] == "Male"])
        female = len(df[df["Gender"] == "Female"])

    overtime = 0

    if "OverTime" in df.columns:
        overtime = len(df[df["OverTime"] == "Yes"])

    department_chart = None

    if "Department" in df.columns:

        dept = df["Department"].value_counts().reset_index()
        dept.columns = ["Department", "Employees"]

        fig = px.bar(
            dept,
            x="Department",
            y="Employees",
            title="Department Distribution"
        )

        department_chart = fig.to_html(full_html=False)

    gender_chart = None

    if "Gender" in df.columns:

        fig = px.pie(
            df,
            names="Gender",
            title="Gender Distribution"
        )

        gender_chart = fig.to_html(full_html=False)

    income_chart = None

    if "MonthlyIncome" in df.columns:

        fig = px.histogram(
            df,
            x="MonthlyIncome",
            title="Monthly Income Distribution"
        )

        income_chart = fig.to_html(full_html=False)

    return render_template(

        "analytics.html",

        total=total,

        avg_age=avg_age,

        avg_income=avg_income,

        male=male,

        female=female,

        overtime=overtime,

        department_chart=department_chart,

        gender_chart=gender_chart,

        income_chart=income_chart

    )
# ==========================================================
# CANDIDATE APPROVAL PAGE
# ==========================================================

@app.route("/candidate")
def candidate():

    global df

    if "user" not in session:
        return redirect(url_for("login_page"))

    if df is None:
        return redirect(url_for("upload"))

    return render_template(
        "candidate.html",
        approved_table=None,
        total=0
    )


# ==========================================================
# FILTER CANDIDATES
# ==========================================================

@app.route("/filter_candidates", methods=["POST"])
def filter_candidates():

    global df

    if "user" not in session:
        return redirect(url_for("login_page"))

    if df is None:
        return redirect(url_for("upload"))

    filtered = df.copy()

    # Age
    if "Age" in filtered.columns:
        min_age = int(request.form.get("age", 0))
        filtered = filtered[filtered["Age"] >= min_age]

    # Experience
    if "TotalWorkingYears" in filtered.columns:
        min_exp = int(request.form.get("experience", 0))
        filtered = filtered[filtered["TotalWorkingYears"] >= min_exp]

    # Salary
    if "MonthlyIncome" in filtered.columns:
        min_salary = int(request.form.get("salary", 0))
        filtered = filtered[filtered["MonthlyIncome"] >= min_salary]

    # Department
    department = request.form.get("department")

    if department and "Department" in filtered.columns:
        filtered = filtered[
            filtered["Department"] == department
        ]

    # Performance Rating
    rating = request.form.get("rating")

    if (
        rating
        and "PerformanceRating" in filtered.columns
    ):
        filtered = filtered[
            filtered["PerformanceRating"] >= int(rating)
        ]

    # Attrition
    attrition = request.form.get("attrition")

    if (
        attrition
        and "Attrition" in filtered.columns
    ):
        filtered = filtered[
            filtered["Attrition"] == attrition
        ]

    # OverTime
    overtime = request.form.get("overtime")

    if (
        overtime
        and "OverTime" in filtered.columns
    ):
        filtered = filtered[
            filtered["OverTime"] == overtime
        ]

    approved_table = filtered.to_html(
        classes="table table-striped table-bordered",
        index=False
    )

    return render_template(
        "candidate.html",
        approved_table=approved_table,
        total=len(filtered)
    )


# ==========================================================
# DOWNLOAD APPROVED CANDIDATES
# ==========================================================

@app.route("/download_candidates", methods=["POST"])
def download_candidates():

    global df

    if "user" not in session:
        return redirect(url_for("login_page"))

    if df is None:
        return redirect(url_for("upload"))

    filtered = df.copy()

    if "Age" in filtered.columns:
        filtered = filtered[
            filtered["Age"] >= int(request.form.get("age", 0))
        ]

    if "TotalWorkingYears" in filtered.columns:
        filtered = filtered[
            filtered["TotalWorkingYears"] >= int(request.form.get("experience", 0))
        ]

    if "MonthlyIncome" in filtered.columns:
        filtered = filtered[
            filtered["MonthlyIncome"] >= int(request.form.get("salary", 0))
        ]

    department = request.form.get("department")

    if department and "Department" in filtered.columns:
        filtered = filtered[
            filtered["Department"] == department
        ]

    output_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        "approved_candidates.csv"
    )

    filtered.to_csv(output_path, index=False)

    return send_file(
        output_path,
        as_attachment=True
    )
# ==========================================================
# DATA WAREHOUSE PAGE
# ==========================================================

@app.route("/warehouse")
def warehouse():

    if "user" not in session:
        return redirect(url_for("login_page"))

    return render_template("warehouse.html")


# ==========================================================
# STAR SCHEMA PAGE
# ==========================================================




# ==========================================================
# WEKA PAGE
# ==========================================================
@app.route('/weka', methods=['GET', 'POST'])
def weka():

    global df

    if df is None or df.empty:
        return render_template(
            'weka.html',
            columns=[],
            result=None,
            error="Please upload a dataset first."
        )

    columns = df.columns.tolist()

    result = None
    error = None

    if request.method == 'POST':

        target_column = request.form.get('target_column')

        if not target_column or target_column not in df.columns:
            error = "Please select a valid target column."

        else:

            try:

                # Create a copy of dataset
                data = df.copy()

                # Remove rows where target is missing
                data = data.dropna(subset=[target_column])

                # Need at least 2 classes
                if data[target_column].nunique() < 2:
                    error = "Selected target column must contain at least 2 different classes."

                else:

                    # Separate input and target
                    X = data.drop(columns=[target_column])
                    y = data[target_column]

                    # Remove EmployeeNumber because it is only an ID
                    if "EmployeeNumber" in X.columns:
                        X = X.drop(columns=["EmployeeNumber"])

                    # Process every input column
                    for column in X.columns:

                        # Text / categorical column
                        if X[column].dtype == "object":

                            X[column] = X[column].fillna("Unknown")

                            encoder = LabelEncoder()

                            X[column] = encoder.fit_transform(
                                X[column].astype(str)
                            )

                        # Numeric column
                        else:

                            X[column] = pd.to_numeric(
                                X[column],
                                errors="coerce"
                            )

                            median_value = X[column].median()

                            if pd.isna(median_value):
                                median_value = 0

                            X[column] = X[column].fillna(
                                median_value
                            )

                    # Convert target values into numbers
                    target_encoder = LabelEncoder()

                    y_encoded = target_encoder.fit_transform(
                        y.astype(str)
                    )

                    # Split dataset
                    X_train, X_test, y_train, y_test = train_test_split(
                        X,
                        y_encoded,
                        test_size=0.25,
                        random_state=42,
                        stratify=y_encoded
                    )

                    # Decision Tree Classification
                    model = DecisionTreeClassifier(
                        random_state=42,
                        max_depth=6
                    )

                    model.fit(X_train, y_train)

                    # Prediction
                    predictions = model.predict(X_test)

                    # Accuracy
                    accuracy = accuracy_score(
                        y_test,
                        predictions
                    ) * 100

                    # Classification Report
                    report = classification_report(
                        y_test,
                        predictions,
                        target_names=target_encoder.classes_,
                        output_dict=True,
                        zero_division=0
                    )

                    # Confusion Matrix
                    matrix = confusion_matrix(
                        y_test,
                        predictions
                    )

                    result = {
                        "target": target_column,
                        "accuracy": round(accuracy, 2),
                        "classes": target_encoder.classes_.tolist(),
                        "report": report,
                        "matrix": matrix.tolist(),
                        "training_records": len(X_train),
                        "testing_records": len(X_test),
                        "total_records": len(data)
                    }

            except Exception as e:
                error = str(e)

    return render_template(
        'weka.html',
        columns=columns,
        result=result,
        error=error
    )



# ==========================================================
# KNIME PAGE
# ==========================================================

@app.route("/knime")
def knime():

    if "user" not in session:
        return redirect(url_for("login_page"))

    return render_template("knime.html")


# ==========================================================
# REPORTS PAGE
# ==========================================================

# ==========================================================
# REPORTS PAGE - DYNAMIC 6 REPORTS
# ==========================================================

@app.route("/reports")
def reports():

    global df

    # Check login
    if "user" not in session:
        return redirect(url_for("login_page"))

    # Check dataset
    if df is None or df.empty:
        return redirect(url_for("upload"))

    # Copy uploaded dataset
    data = df.copy()

    # ======================================================
    # GET FILTER VALUES
    # ======================================================

    selected_department = request.args.get("department", "All")
    selected_gender = request.args.get("gender", "All")
    selected_attrition = request.args.get("attrition", "All")

    # ======================================================
    # APPLY FILTERS
    # ======================================================

    if selected_department != "All" and "Department" in data.columns:
        data = data[data["Department"].astype(str) == selected_department]

    if selected_gender != "All" and "Gender" in data.columns:
        data = data[data["Gender"].astype(str) == selected_gender]

    if selected_attrition != "All" and "Attrition" in data.columns:
        data = data[data["Attrition"].astype(str) == selected_attrition]

    # ======================================================
    # DROPDOWN VALUES FROM ORIGINAL DATASET
    # ======================================================

    departments = []
    genders = []
    attritions = []

    if "Department" in df.columns:
        departments = sorted(
            df["Department"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    if "Gender" in df.columns:
        genders = sorted(
            df["Gender"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    if "Attrition" in df.columns:
        attritions = sorted(
            df["Attrition"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    # List to store all graphs
    charts = []


    # ======================================================
    # REPORT 1 - DEPARTMENT-WISE EMPLOYEE COUNT
    # ======================================================

    if "Department" in data.columns:

        temp = (
            data.groupby("Department")
            .size()
            .reset_index(name="Employee Count")
        )

        fig = px.bar(
            temp,
            x="Department",
            y="Employee Count",
            title="Department-wise Employee Count"
        )

        fig.update_layout(
            height=420,
            margin=dict(l=50, r=30, t=60, b=80)
        )

        charts.append({
            "id": "chart1",
            "title": "Department-wise Employee Count",
            "graph": fig.to_html(
                full_html=False,
                include_plotlyjs=False,
                div_id="chart1",
                config={"responsive": True}
            )
        })


    # ======================================================
    # REPORT 2 - GENDER-WISE EMPLOYEE DISTRIBUTION
    # ======================================================

    if "Gender" in data.columns:

        temp = (
            data.groupby("Gender")
            .size()
            .reset_index(name="Employee Count")
        )

        fig = px.pie(
            temp,
            names="Gender",
            values="Employee Count",
            title="Gender-wise Employee Distribution"
        )

        fig.update_layout(
            height=420,
            margin=dict(l=30, r=30, t=60, b=30)
        )

        charts.append({
            "id": "chart2",
            "title": "Gender-wise Employee Distribution",
            "graph": fig.to_html(
                full_html=False,
                include_plotlyjs=False,
                div_id="chart2",
                config={"responsive": True}
            )
        })


    # ======================================================
    # REPORT 3 - ATTRITION ANALYSIS BY DEPARTMENT
    # ======================================================

    if "Department" in data.columns and "Attrition" in data.columns:

        temp = (
            data.groupby(["Department", "Attrition"])
            .size()
            .reset_index(name="Employee Count")
        )

        fig = px.bar(
            temp,
            x="Department",
            y="Employee Count",
            color="Attrition",
            barmode="group",
            title="Attrition Analysis by Department"
        )

        fig.update_layout(
            height=420,
            margin=dict(l=50, r=30, t=60, b=80)
        )

        charts.append({
            "id": "chart3",
            "title": "Attrition Analysis by Department",
            "graph": fig.to_html(
                full_html=False,
                include_plotlyjs=False,
                div_id="chart3",
                config={"responsive": True}
            )
        })


    # ======================================================
    # REPORT 4 - AVERAGE MONTHLY INCOME BY DEPARTMENT
    # ======================================================

    if "Department" in data.columns and "MonthlyIncome" in data.columns:

        temp = (
            data.groupby("Department")["MonthlyIncome"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            temp,
            x="Department",
            y="MonthlyIncome",
            title="Average Monthly Income by Department"
        )

        fig.update_layout(
            height=420,
            margin=dict(l=50, r=30, t=60, b=80)
        )

        charts.append({
            "id": "chart4",
            "title": "Average Monthly Income by Department",
            "graph": fig.to_html(
                full_html=False,
                include_plotlyjs=False,
                div_id="chart4",
                config={"responsive": True}
            )
        })


    # ======================================================
    # REPORT 5 - AVERAGE EXPERIENCE BY JOB ROLE
    # ======================================================

    if "JobRole" in data.columns and "TotalWorkingYears" in data.columns:

        temp = (
            data.groupby("JobRole")["TotalWorkingYears"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            temp,
            x="JobRole",
            y="TotalWorkingYears",
            title="Average Experience by Job Role"
        )

        fig.update_layout(
            height=420,
            margin=dict(l=50, r=30, t=60, b=130),
            xaxis_tickangle=-35
        )

        charts.append({
            "id": "chart5",
            "title": "Average Experience by Job Role",
            "graph": fig.to_html(
                full_html=False,
                include_plotlyjs=False,
                div_id="chart5",
                config={"responsive": True}
            )
        })


    # ======================================================
    # REPORT 6 - AVERAGE JOB LEVEL BY DEPARTMENT
    # ======================================================

    if "Department" in data.columns and "JobLevel" in data.columns:

        temp = (
            data.groupby("Department")["JobLevel"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            temp,
            x="Department",
            y="JobLevel",
            title="Average Job Level by Department"
        )

        fig.update_layout(
            height=420,
            margin=dict(l=50, r=30, t=60, b=80)
        )

        charts.append({
            "id": "chart6",
            "title": "Average Job Level by Department",
            "graph": fig.to_html(
                full_html=False,
                include_plotlyjs=False,
                div_id="chart6",
                config={"responsive": True}
            )
        })


    # ======================================================
    # SEND EVERYTHING TO reports.html
    # ======================================================

    return render_template(
        "reports.html",
        charts=charts,
        departments=departments,
        genders=genders,
        attritions=attritions,
        selected_department=selected_department,
        selected_gender=selected_gender,
        selected_attrition=selected_attrition,
        record_count=len(data)
    )

# ==========================================================
# APPLICATION STATUS
# ==========================================================

@app.route("/status")
def status():

    return {
        "Application": "Enterprise HR Analytics",
        "Status": "Running",
        "Dataset Loaded": df is not None
    }


# ==========================================================
# ERROR 404
# ==========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template("404.html"), 404


# ==========================================================
# ERROR 500
# ==========================================================

@app.errorhandler(500)
def internal_server_error(error):

    return """
    <h1>500 Internal Server Error</h1>
    <h3>Something went wrong.</h3>
    <a href='/dashboard'>Return to Dashboard</a>
    """, 500


# ==========================================================
# RUN APPLICATION
# ==========================================================
@app.route("/olap")
def olap():

    if df is None or df.empty:
        return "Please upload a dataset first."

    data = df.copy()

    columns = data.columns.tolist()

    cube_data = data[columns].copy()
    cube_data = cube_data.head(500)

    return render_template(
    "olap.html",
    data=cube_data.to_dict(orient="records"),
    columns=columns
)

# ============================================================
# HELPER: GET CURRENT DATASET
# ============================================================

def get_schema_dataframe():
    global df

    if df is None or df.empty:
        return None

    return df.copy()


# ============================================================
# HELPER: CREATE SAFE TABLE NAME
# ============================================================

def safe_table_name(name):
    name = str(name).strip()
    name = name.replace(" ", "_")
    name = name.replace("-", "_")
    name = name.replace("/", "_")
    return name.upper()


# ============================================================
# HELPER: DETECT MEASURES AND DIMENSIONS DYNAMICALLY
# ============================================================

def detect_schema_columns(data):

    numeric_columns = data.select_dtypes(include=["number"]).columns.tolist()

    categorical_columns = [
        column for column in data.columns
        if column not in numeric_columns
    ]

    # Remove ID-like columns from measures
    id_columns = []

    for column in data.columns:

        column_name = str(column).lower()

        if (
            column_name == "id"
            or column_name.endswith("id")
            or "number" in column_name
            or "employee" in column_name
        ):
            id_columns.append(column)

    measures = [
        column for column in numeric_columns
        if column not in id_columns
    ]

    dimensions = [
        column for column in categorical_columns
        if column not in id_columns
    ]

    # If there are too few categorical columns,
    # use non-ID numeric columns as additional dimensions
    if len(dimensions) < 2:

        for column in numeric_columns:

            if column not in measures and column not in dimensions:
                dimensions.append(column)

    # Limit displayed dimensions so the diagram remains clear
    dimensions = dimensions[:10]

    # Limit measures
    measures = measures[:8]

    return dimensions, measures


# ============================================================
# STAR SCHEMA GRAPH
# ============================================================

def create_star_schema_graph(data):

    dimensions, measures = detect_schema_columns(data)

    fig = go.Figure()

    # --------------------------------------------------------
    # CENTRAL FACT TABLE
    # --------------------------------------------------------

    fact_name = "FACT_DATA_ANALYTICS"

    fact_columns = []

    for dimension in dimensions:
        fact_columns.append(
            "FK_" + safe_table_name(dimension)
        )

    for measure in measures:
        fact_columns.append(
            safe_table_name(measure)
        )

    if not fact_columns:
        fact_columns = ["RECORD_COUNT"]

    fact_text = (
        "<b>" + fact_name + "</b><br>"
        + "<br>".join(fact_columns[:12])
    )

    # Centre position
    fact_x = 0
    fact_y = 0

    # --------------------------------------------------------
    # DIMENSION POSITIONS SPREAD AROUND THE FACT TABLE
    # --------------------------------------------------------

    total_dimensions = len(dimensions)

    if total_dimensions == 0:

        fig.add_annotation(
            x=0,
            y=0,
            text=(
                "<b>FACT_DATA_ANALYTICS</b><br>"
                "RECORD_COUNT"
            ),
            showarrow=False,
            font=dict(size=18),
            bgcolor="#1f4e78",
            bordercolor="#0f2f4a",
            borderwidth=2,
            font_color="white",
            borderpad=18
        )

    else:

        radius_x = 8
        radius_y = 5.5

        for index, dimension in enumerate(dimensions):

            angle = (
                2 * math.pi * index / total_dimensions
            )

            dimension_x = radius_x * math.cos(angle)
            dimension_y = radius_y * math.sin(angle)

            dimension_table = (
                "DIM_" + safe_table_name(dimension)
            )

            # Dynamic dimension information
            unique_values = data[dimension].nunique()

            dimension_text = (
                "<b>" + dimension_table + "</b><br>"
                + "PK_" + safe_table_name(dimension) + "<br>"
                + safe_table_name(dimension) + "<br>"
                + "Unique Values: " + str(unique_values)
            )

            # Connection from FACT TABLE to DIMENSION
            fig.add_shape(
                type="line",
                x0=fact_x,
                y0=fact_y,
                x1=dimension_x,
                y1=dimension_y,
                line=dict(
                    color="#6b7280",
                    width=2
                )
            )

            # Dimension table
            fig.add_annotation(
                x=dimension_x,
                y=dimension_y,
                text=dimension_text,
                showarrow=False,
                align="left",
                font=dict(size=13),
                bgcolor="#dbeafe",
                bordercolor="#2563eb",
                borderwidth=2,
                borderpad=14
            )

        # FACT TABLE LAST SO IT STANDS OUT
        fig.add_annotation(
            x=fact_x,
            y=fact_y,
            text=fact_text,
            showarrow=False,
            align="left",
            font=dict(size=14),
            bgcolor="#1f4e78",
            bordercolor="#0f2f4a",
            borderwidth=3,
            font_color="white",
            borderpad=18
        )

    fig.update_layout(
        title={
            "text": "Dynamic Star Schema",
            "x": 0.5,
            "xanchor": "center"
        },
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(
            l=50,
            r=50,
            t=80,
            b=50
        ),
        xaxis=dict(
            visible=False,
            range=[-11, 11]
        ),
        yaxis=dict(
            visible=False,
            range=[-8, 8]
        ),
        height=750
    )

    return fig


# ============================================================
# SNOWFLAKE SCHEMA GRAPH
# ============================================================

def create_snowflake_schema_graph(data):

    dimensions, measures = detect_schema_columns(data)

    fig = go.Figure()

    fact_name = "FACT_DATA_ANALYTICS"

    fact_columns = []

    for dimension in dimensions:
        fact_columns.append(
            "FK_" + safe_table_name(dimension)
        )

    for measure in measures:
        fact_columns.append(
            safe_table_name(measure)
        )

    if not fact_columns:
        fact_columns = ["RECORD_COUNT"]

    fact_text = (
        "<b>" + fact_name + "</b><br>"
        + "<br>".join(fact_columns[:12])
    )

    fact_x = 0
    fact_y = 0

    total_dimensions = len(dimensions)

    if total_dimensions == 0:

        fig.add_annotation(
            x=0,
            y=0,
            text=fact_text,
            showarrow=False,
            bgcolor="#1f4e78",
            bordercolor="#0f2f4a",
            borderwidth=3,
            borderpad=18,
            font=dict(
                size=16,
                color="white"
            )
        )

    else:

        # Main dimensions are around the FACT table
        main_radius_x = 7
        main_radius_y = 5

        # Child normalized tables are further outside
        child_radius_x = 11
        child_radius_y = 7.5

        for index, dimension in enumerate(dimensions):

            angle = (
                2 * math.pi * index / total_dimensions
            )

            # MAIN DIMENSION POSITION
            dimension_x = (
                main_radius_x * math.cos(angle)
            )

            dimension_y = (
                main_radius_y * math.sin(angle)
            )

            # CHILD DIMENSION POSITION
            child_x = (
                child_radius_x * math.cos(angle)
            )

            child_y = (
                child_radius_y * math.sin(angle)
            )

            dimension_table = (
                "DIM_" + safe_table_name(dimension)
            )

            child_table = (
                "DETAIL_" + safe_table_name(dimension)
            )

            unique_values = data[dimension].nunique()

            # ------------------------------------------------
            # FACT TABLE -> MAIN DIMENSION
            # ------------------------------------------------

            fig.add_shape(
                type="line",
                x0=fact_x,
                y0=fact_y,
                x1=dimension_x,
                y1=dimension_y,
                line=dict(
                    color="#6b7280",
                    width=2
                )
            )

            # ------------------------------------------------
            # MAIN DIMENSION -> NORMALIZED CHILD TABLE
            # ------------------------------------------------

            fig.add_shape(
                type="line",
                x0=dimension_x,
                y0=dimension_y,
                x1=child_x,
                y1=child_y,
                line=dict(
                    color="#16a34a",
                    width=2,
                    dash="dot"
                )
            )

            # MAIN DIMENSION
            dimension_text = (
                "<b>" + dimension_table + "</b><br>"
                + "PK_" + safe_table_name(dimension) + "<br>"
                + safe_table_name(dimension)
            )

            fig.add_annotation(
                x=dimension_x,
                y=dimension_y,
                text=dimension_text,
                showarrow=False,
                align="left",
                bgcolor="#dbeafe",
                bordercolor="#2563eb",
                borderwidth=2,
                borderpad=12,
                font=dict(size=12)
            )

            # NORMALIZED / BRANCH DIMENSION
            child_text = (
                "<b>" + child_table + "</b><br>"
                + "PK_DETAIL_ID<br>"
                + safe_table_name(dimension) + "_DETAIL<br>"
                + "Unique Values: " + str(unique_values)
            )

            fig.add_annotation(
                x=child_x,
                y=child_y,
                text=child_text,
                showarrow=False,
                align="left",
                bgcolor="#dcfce7",
                bordercolor="#16a34a",
                borderwidth=2,
                borderpad=12,
                font=dict(size=11)
            )

        # CENTRAL FACT TABLE
        fig.add_annotation(
            x=fact_x,
            y=fact_y,
            text=fact_text,
            showarrow=False,
            align="left",
            bgcolor="#1f4e78",
            bordercolor="#0f2f4a",
            borderwidth=3,
            borderpad=18,
            font=dict(
                size=14,
                color="white"
            )
        )

    fig.update_layout(
        title={
            "text": "Dynamic Snowflake Schema",
            "x": 0.5,
            "xanchor": "center"
        },
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(
            l=50,
            r=50,
            t=80,
            b=50
        ),
        xaxis=dict(
            visible=False,
            range=[-15, 15]
        ),
        yaxis=dict(
            visible=False,
            range=[-11, 11]
        ),
        height=850
    )

    return fig


# ============================================================
# STAR SCHEMA PAGE
# ============================================================

@app.route("/star_schema")
def star_schema():

    if "user" not in session:
        return redirect(url_for("login"))

    data = get_schema_dataframe()

    if data is None:
        return render_template(
            "schema_dynamic.html",
            schema_type="Star Schema",
            error_message="Please upload a dataset first."
        )

    dimensions, measures = detect_schema_columns(data)

    fig = create_star_schema_graph(data)

    graph_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn"
    )

    return render_template(
        "schema_dynamic.html",
        schema_type="Dynamic Star Schema",
        graph=graph_html,
        dimensions=dimensions,
        measures=measures,
        total_records=len(data),
        total_columns=len(data.columns)
    )


# ============================================================
# SNOWFLAKE SCHEMA PAGE
# ============================================================

@app.route("/snowflake_schema")
def snowflake_schema():

    if "user" not in session:
        return redirect(url_for("login"))

    data = get_schema_dataframe()

    if data is None:
        return render_template(
            "schema_dynamic.html",
            schema_type="Snowflake Schema",
            error_message="Please upload a dataset first."
        )

    dimensions, measures = detect_schema_columns(data)

    fig = create_snowflake_schema_graph(data)

    graph_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn"
    )

    return render_template(
        "schema_dynamic.html",
        schema_type="Dynamic Snowflake Schema",
        graph=graph_html,
        dimensions=dimensions,
        measures=measures,
        total_records=len(data),
        total_columns=len(data.columns)
    )

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
