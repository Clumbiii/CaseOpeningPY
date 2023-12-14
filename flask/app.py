from datetime import datetime
from hashlib import sha512
from uuid import uuid4 as uuid
from flask import Flask, redirect, request, render_template, make_response
from database import dbms as case_opening_instance

dbms = case_opening_instance()
dbms.createTables()

app = Flask(__name__)


########## Pages ##########
@app.route('/')
def page():
    logged_in, profil_info = fetch_user_data(request.cookies.get('session_code'))

    return render_template("spin.html", profil_info=profil_info, login=logged_in)

 
@app.route('/settings')
@app.route('/settings/<int:userid>', methods=['GET','POST'])
def page_settings(userid: int):
    logged_in, profil_info = fetch_user_data(request.cookies.get('session_code'))

    if not logged_in:
        return make_response(redirect('/'))
    
    if userid == 0:
        return make_response(redirect(f"/settings/{profil_info[0]}"))
    
    res, page_profil_info = dbms.fetch_user_data(userid)

    entries, total_count, entries_exist = dbms.get_user_history(userid)

    if not res:
        return show_error(page_profil_info)
    
    if request.method == 'POST':
        match request.form['new_value']:
            case "change_password":
                old_passhash = sha512(request.form['old-pass'].encode()).hexdigest()

                if not old_passhash.lower() == dbms.get_passhash_for_user(userid):
                    return show_error("Das alte Passwort ist falsch.")
                
                new_password = request.form['new-pass']
                conf_password = request.form['conf-pass']

                new_passwordHashed = sha512(new_password.encode()).hexdigest()

                if not new_password == conf_password:
                    return show_error("Die neuen Passwörter stimmen nicht überein.")
                else:
                    dbms.update_password(userid, new_passwordHashed)
                    return make_response(redirect(f"/settings/{userid}"))

            case "change_displayname":
                input_newname = request.form['displayname']
                if input_newname == "" or input_newname == None:
                     return show_error("Bitte gib einen Spitznamen an.")
                
                dbms.update_nickname(userid, request.form['displayname'])
                return make_response(redirect(f"/settings/{userid}"))


            case "delete_account":
                input_password = request.form['deleteaccount-password']
                input_passwordHashed = sha512(input_password.encode()).hexdigest()

                if input_passwordHashed == dbms.get_passhash_for_user(userid):
                    dbms.delete_account(userid)
                    page_logout()
                else:
                    return show_error("Dieses Passwort ist falsch.")

            case _:
                return make_response(redirect(f"/settings/{userid}"))
            
        if not res:
            return show_error("Diese Aktion kann nicht zugeordnet werden.")
        else:
            return make_response(redirect('/'))

    return render_template("settings.html", login=logged_in,profil_info=page_profil_info, total_count=total_count)


@app.route('/login', methods=["GET","POST"])
def page_login():    
    if request.method == 'POST':
        username = request.form['username']

        login_passhash = sha512(request.form['password'].encode()).hexdigest()

        res, userid, dbms_passhash = dbms.get_passhash(username)

        if not res:
            return show_error(userid)
        

        if dbms.exist_username(username) and not login_passhash == dbms_passhash:
            dbms.add_failed_login(userid)
            return show_error("Dieses Passwort ist falsch.")


        if login_passhash == dbms_passhash:
            lifetime = 3000000
            sesskey = str(uuid())
            color = "default"

            dbms.set_sesskey(sesskey, userid, lifetime)
            dbms.add_login(userid)

            response = setcookie("session_code", sesskey, color)
            return response
        else:
            return show_error("Dieses Passwort ist falsch.")
    else:
        return render_template("login.html")


@app.route('/spin', methods=["GET","POST"])
def page_spin():
    sesskey = request.cookies.get('session_code')
    logged_in, profil_info = fetch_user_data(sesskey)
    return render_template("spin.html", profil_info=profil_info, login=logged_in)


@app.route('/add_history', methods=['POST'])
def page_callback_history():
    sesskey = request.cookies.get('session_code')
    logged_in, userid =  dbms.check_sesskey(sesskey)

    data = request.get_json()
    wonrarity = data['wonrarity']
    wonname = data['wonname']
    wondisplay = data['wondisplay']
    woncolor = data['woncolor']

    dbms.add_history(userid, wonrarity, wonname, wondisplay)
    dbms.remove_case(userid)

    return update_color(woncolor)


@app.route('/shop', methods=["GET","POST"])
def page_shop():
    sesskey = request.cookies.get('session_code')
    logged_in, profil_info = fetch_user_data(sesskey)
    return render_template("shop.html", profil_info=profil_info, login=logged_in)


@app.route('/history', methods=["GET","POST"])
def page_history():
    sesskey = request.cookies.get('session_code')
    logged_in, profil_info = fetch_user_data(sesskey)

    userid = dbms.get_userid_by_session_key(sesskey)
    entries, total_count, entries_exist = dbms.get_user_history(userid)

    if not entries_exist:
        return render_template("history.html", profil_info=profil_info, login=logged_in, entries=None)
    else:
        return render_template("history.html", profil_info=profil_info, login=logged_in, entries=entries)


@app.route('/logout')
def page_logout():
    sesskey = request.cookies.get('session_code')
    logged_in, profil_info = fetch_user_data(sesskey)

    if not logged_in:
        return make_response(redirect('/login'))
    
    dbms.logout_user(sesskey)

    delete_cookie('session_code')

    return make_response(redirect('/'))
########## Pages ##########



########## Used Methods ##########
def show_error(message, errorcode:int=400):
    return render_template("error.html", message=message, errorcode=errorcode)


def fetch_user_data(sesskey: str):
    if not sesskey:
        return False, ()
    
    logged_in, userid = dbms.check_sesskey(sesskey)
    
    if logged_in:
        res, profil_info = dbms.fetch_user_data(userid)
        
        if not res:
            return show_error(profil_info)
    else:
        profil_info = ()
    return logged_in, profil_info
########## Data Section ##########



########## Cookie Section ##########
def setcookie(name: str, value: str, color: str = "default"):
    response = make_response(redirect('/'))

    response.set_cookie(name, value, max_age=3000000)
    response.set_cookie("session_color", color, max_age=3000000)
    return response


def delete_cookie(name: str):
    response = make_response(redirect('/'))

    response.set_cookie(name, '', expires=0)
    return response


def update_color(color: str):
    response = make_response(redirect('/'))

    response.set_cookie("session_color", color)
    return response
########## Cookie Section ##########

if __name__ == '__main__':
    app.run()