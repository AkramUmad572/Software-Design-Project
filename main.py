from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/pythonlogin", methods=["GET", "POST"])
def pythonlogin():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        form_type = request.form.get("form_type")

        print("----------- USER INPUT -----------")
        print("FORM:", form_type)
        print("USERNAME:", username)
        print("PASSWORD:", password)
        print("----------------------------------")

    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)