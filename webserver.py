from flask import Flask, render_template, jsonify, session, redirect, request
from flask_session import Session
import mysql.connector
import search
import json
from rake_nltk import Rake

sql = mysql.connector.connect(
        host="localhost",
        user="search",
        password="",
        database="search_engine",
        pool_name="sqlPool",
        pool_size=20
    )
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
r = Rake()

# Suppresses 404s by returning a blank page instead
@app.errorhandler(404)
def invalid_path(error):
    return ""

# Renders the homepage
@app.route("/")
def homepage():
    return render_template("home.html")

# Flask is garbage so this route is used for empty queries
@app.route("/query/")
def no_query():
    return jsonify(list())

# Renders the ads creation page
@app.route("/ads", methods=["GET"])
def get_ads():
    if not session.get("loggedin"):
        return redirect("/")
    else:
        query = sql.cursor()
        query.execute("SELECT balance FROM users WHERE id = %s", (session["uid"],))
        res = query.fetchone()
        sql.commit()
        query.close()
        return render_template("createads.html", data=res)

# Adds the ad to the database
@app.route("/ads", methods=["POST"])
def create_ads():
    if not session.get("loggedin"):
        return "Log in first!", 400
    elif request.values.get("title") and request.values.get("body") and request.values.get("site") and request.values.get("cpc") and request.values.get("keywords[0][tag]"):
        try:
            query = sql.cursor()
            query.execute("INSERT INTO ads (title, content, url, user_id) VALUES (%s, %s, %s, %s)", (request.values.get("title"), request.values.get("body"), request.values.get("site"), session["uid"]))
            l = query.lastrowid
            counter = 0
            while True:
                if request.values.get("keywords[" + str(counter) + "][tag]") == None:
                    break
                query.execute("INSERT INTO ads_keywords (ad_id, word, cpc) VALUES (%s, %s, %s)", (l,request.values.get("keywords[" + str(counter) + "][tag]"), request.values.get("cpc")))
                counter += 1
            sql.commit()
            query.close()
            return "Thanks for submitting the ad!"
        except:
            return "bad input!", 400
    else:
        return "bad input!", 400

# Fetch search suggestions as the user types, if they stop typing for some reason in the middle
@app.route("/query/<input>")
def query_db(input):
    input = input.split(" ")
    query = sql.cursor()
    query.execute("SELECT * FROM terms WHERE content LIKE %s LIMIT 5", ("%".join(input) + "%",))
    result = query.fetchall()
    sql.commit()
    query.close()
    return jsonify(result)

# Render the search results page along with potential ads that are associated with it
@app.route("/search/<input>")
def search_page(input):
    query = sql.cursor()
    d = list()
    a = list()
    r.extract_keywords_from_text(input)
    w = r.get_ranked_phrases()
    for word in w:
        query.execute("SELECT * FROM ads_keywords, ads WHERE word = %s AND ads_keywords.ad_id = ads.id ORDER BY cpc DESC", (word,))
        results = query.fetchall()
        sql.commit()
        if results:
            for result in results:
                query.execute("SELECT balance FROM users, ads, ads_keywords WHERE users.id = ads.user_id AND ads.id = ads_keywords.ad_id AND ads_keywords.word = %s LIMIT 1", (result[1],))
                res = query.fetchone()
                sql.commit()
                if res[0] > result[2]:
                    a.append("<span class=\"badge bg-warning text-dark\">Ad</span>" + result[4])
                    a.append(result[5])
                    a.append(result[6])
                    a.append("ad:" + str(result[0]) + ":" + result[1])
                    break
            break
    q = search.buildDocDictionary(input.split(" "))
    if len(q) > 0:
        tdidfDict = {}
        for term in q:
            #for each term, calculate the partial td-idf in each document it appears in 
            for k,v in q[term].items():
                temp_weight = search.findTdidfWeight(term,k,v)
                if(k not in tdidfDict):
                    tdidfDict[k] = temp_weight
                else:
                    tdidfDict[k] += temp_weight
        sort = sorted(tdidfDict, key=tdidfDict.get, reverse=True)
        sort = sort[0:5]
        print(sort)
        urls = search.find_urlsSE(sort)
        d = search.searchEngineData(urls)
        if len(a) > 0:
            d.insert(0, a)
    if session.get("loggedin") == True:
        query.execute("SELECT * FROM users_searches WHERE search = %s AND user_id = %s", (input, session["uid"]))
        res2 = query.fetchone()
        if res2:
            query.execute("UPDATE users_searches SET count = count + 1 WHERE search = %s AND user_id = %s", (input, session["uid"]))
            sql.commit()
        else:
            query.execute("INSERT INTO users_searches (user_id, search, count) VALUES (%s, %s, 1)", (session["uid"], input))
            sql.commit()
    query.close()
    return render_template("searchresults.html", data=d)

# Renders the web page by fetching the JSON file associated with it, if its a result, OR if its an ad, redirect the user to the ad page
@app.route("/render/<path:input>")
def render_page(input):
    if input[:3] == "ad:":
        frags = input.split(":")
        if len(frags) < 3:
            return 'Badly formatted URL', 400
        try:
            query = sql.cursor()
            query.execute("SELECT users.id, ads.url, ads_keywords.cpc FROM users,ads,ads_keywords WHERE ads.id = %s AND ads.user_id = users.id AND ads.id = ads_keywords.ad_id AND ads_keywords.word = %s LIMIT 1", (frags[1],frags[2]))
            res = query.fetchone()
            query.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (res[2], res[0]))
            sql.commit()
            # Record ad clicks for potential analytics data
            if session.get("loggedin") == True:
                query.execute("SELECT * FROM users_clicks WHERE click = %s AND user_id = %s LIMIT 1", (input, session["uid"]))
                res2 = query.fetchone()
                if res2:
                    query.execute("UPDATE users_clicks SET count = count + 1 WHERE click = %s AND user_id = %s", (input, session["uid"]))
                    sql.commit()
                else:
                    query.execute("INSERT INTO users_clicks (user_id, click, count, type) VALUES (%s, %s, 1, 'Ad')", (session["uid"], input))
                    sql.commit()
            query.close()
            return redirect(res[1])
        except:
            return 'Ad Owner ran out of money', 400
    else:
        try:
            query = sql.cursor()
            # Record clicks to manipulate the next time the user enters the same search query
            if session.get("loggedin") == True:
                query.execute("SELECT * FROM users_clicks WHERE click = %s AND user_id = %s LIMIT 1", (input, session["uid"]))
                res = query.fetchone()
                if res:
                    query.execute("UPDATE users_clicks SET count = count + 1 WHERE click = %s AND user_id = %s", (input, session["uid"]))
                    sql.commit()
                else:
                    query.execute("INSERT INTO users_clicks (user_id, click, count, type) VALUES (%s, %s, 1, 'Result')", (session["uid"], input))
                    sql.commit()
            query.close()
            with open(input) as f:
                data = json.load(f)
            return data["content"]
        except:
            return "Invalid file path"

# Renders the login page
@app.route("/login", methods=["GET"])
def login():
    if session.get("loggedin"):
        return redirect("/")
    return render_template("login.html")

# Renders the registration page
@app.route("/register", methods=["GET"])
def register():
    if session.get("loggedin"):
        return redirect("/")
    return render_template("register.html")

# Basic login function with no password hashing
@app.route("/login", methods=["POST"])
def login_auth():
    if session.get("loggedin"):
        return 'Already logged in!', 400
    if request.form.get("email") and request.form.get("password"):
        query = sql.cursor()
        query.execute("SELECT * FROM users WHERE email = %s AND password = %s", (request.form.get("email"), request.form.get("password")))
        result = query.fetchone()
        if result:
            session["loggedin"] = True
            session["uid"] = result[0]
            session["user"] = request.form.get("email")
            query.close()
            return 'Success!'
        else:
            query.close()
            return 'Invalid credentials!', 401
    else:
        return 'Invalid credentials!', 401

# Basic registration function with no password hashing
@app.route("/register", methods=["POST"])
def register_auth():
    if session.get("loggedin"):
        return 'Already logged in!', 401
    if request.form.get("email") and request.form.get("password"):
        query = sql.cursor()
        query.execute("SELECT * FROM users WHERE email = %s", (request.form.get("email"),))
        result = query.fetchone()
        if result:
            query.close()
            return 'User exists!', 401
        else:
            query.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (request.form.get("email"), request.form.get("password")))
            sql.commit()
            session["loggedin"] = True
            session["uid"] = query.lastrowid
            session["user"] = request.form.get("email")
            query.close()
            return 'Success!'
    else:
        return 'Invalid request!', 401

# Logs the user out by destroying the session
@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
    search.searchInit()
    app.run()