from flask import Flask, json, Response, request, render_template
from werkzeug.utils import secure_filename
from os import path, getcwd, remove
from datetime import date
import time
from db import Database
from face import Face

app = Flask(__name__, template_folder='template')
app.config['file_allowed'] = ['image/png', 'image/jpeg', 'image/jpg']
app.config['storage'] = path.join(getcwd(), 'storage')
app.db = Database()
app.face = Face(app)

app.unknown_user_id = ''
app.subject = ''


def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)


def check_user(en_no):
    result = app.db.select('SELECT count(*) from users where id = ?', en_no)
    return result[0]


def get_user_by_id(user_id):
    user = {}
    results = app.db.select(
        'SELECT users.id, users.name, users.created, faces.id, faces.user_id, faces.filename,faces.created FROM users LEFT JOIN faces ON faces.user_id = users.id WHERE users.id = ?',
        [user_id])

    index = 0
    for row in results:
        face = {
            "id": row[3],
            "user_id": row[4],
            "filename": row[5],
            "created": row[6],
        }

        if index == 0:
            user = {
                "id": row[0],
                "name": row[1],
                "created": row[2],
                "faces": [],
            }

        if row[3]:
            user["faces"].append(face)
        index = index + 1

    if 'id' in user:
        return user
    return None


def delete_user_by_id(user_id):
    app.db.delete('DELETE FROM users WHERE users.id = ?', [user_id])
    # also delete all faces with user id
    app.db.delete('DELETE FROM faces WHERE faces.user_id = ?', [user_id])


#  Route for Homepage
@app.route('/', methods=['GET'])
def page_home():
    return render_template('index.html')


@app.route('/api', methods=['GET'])
def homepage():
    output = json.dumps({"api": '1.0'})
    return success_handle(output)


@app.route('/api/train', methods=['POST'])
def train():
    output = json.dumps({"success": True})

    if 'file' not in request.files:
        print("Face image is required")
        return error_handle("Face image is required.")

    else:
        print("File request", request.files)
        file = request.files['file']

        if file.mimetype not in app.config['file_allowed']:
            print("File extension is not allowed")
            return error_handle("We only allow file upload with *.png and *.jpeg")

        else:
            # get details in form data
            print("Request contain image")
            name = request.form['name']
            en_no = request.form['en_no']
            print("Information of that image, Name:  ?\t Enrollment number: ?", name, en_no)
            print("File is allowed and will be saved in ", app.config['storage'])
            filename = secure_filename(file.filename)
            trained_storage = path.join(app.config['storage'], 'trained')
            filename2 = en_no +'_'+filename
            file.save(path.join(trained_storage, filename2))

            if check_user(en_no):
                print("Student already exists")
                remove(path.join(trained_storage, filename))
                return error_handle("Student already exists")
            else:
                if app.face.check_face(filename):
                    # Saving in database
                    created = int(time.time())
                    user_id = app.db.insert('INSERT INTO users(id, name, created) values(?,?,?)', [en_no, name, created])

                    if user_id:
                        print("User's data is saved: ", name, user_id)
                        #   user has been saved with user_id, and now we need save faces table as well
                        face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) values(?,?,?)', [user_id, en_no+'_'+filename, created])

                        if face_id:
                            print("Face has been saved")
                            face_data = {"id": face_id, "filename": filename, "created": created}
                            return_output = json.dumps({"id": user_id, "name": name, "face": [face_data]})
                            return success_handle(return_output)

                        else:
                            print("Error occurred while saving face")
                            return error_handle("An error occurred while saving face")

                    else:
                        print("Something happened")
                        return error_handle("An error occurred while inserting new user")

                else:
                    print("The image does not contain a face")
                    remove(path.join(trained_storage, filename))
                    return error_handle("The image does not contain a face")

    return success_handle(output)


# Route for user profile
@app.route('/api/users/<int:user_id>', methods=['GET', 'DELETE'])
def user_profile(user_id):

    if request.method == 'GET':
        user = get_user_by_id(user_id)

        if user:
            return success_handle(json.dumps(user), 200)
        else:
            return error_handle("User not found", 404)

    if request.method == 'DELETE':
        delete_user_by_id(user_id)
        return success_handle(json.dumps({"deleted": True}))


# Route for recognizing unknown face
@app.route('/api/recognize', methods=['POST'])
def recognize():
    if 'file' not in request.files:
        return error_handle("Image is required")

    else:
        file = request.files['file']

        # file extension validate
        if file.mimetype not in app.config['file_allowed']:
            return error_handle("File extension is not allowed")

        else:
            app.face.load_all()
            filename = secure_filename(file.filename)
            unknown_storage = path.join(app.config["storage"], 'unknown')
            file_path = path.join(unknown_storage, filename)
            file.save(file_path)
            app.unknown_user_id = app.face.recognize(filename)
            app.subject = request.form['subject']
            remove(file_path)

            if app.unknown_user_id:
                message = {"message": "{0} is present".format(app.unknown_user_id)}
                return success_handle(json.dumps(message))

            else:
                return error_handle("Sorry! We did not found you, try again")


# Route for confirm
@app.route('/api/confirm', methods=['GET'])
def confirm():
    if app.unknown_user_id:
        confirm_att = request.form['confirm_att']
        today = date.today().strftime("%Y-%m-%d")

        if confirm_att:
            subjects = app.db.show_tables()

            if app.subject not in subjects:
                app.db.create_subject(app.subject)

            app.db.insert('INSERT INTO ?(student, date) values(?,?)', [app.subject, app.unknown_user_id, today])
            app.unknown_user_id = ''
            app.subject = ''
            message = {"message": "Attendance marked for: ".format(app.unknown_user_id)}
            return success_handle(json.dumps(message))

    return error_handle("Sorry! We did not found you, try again")


# Run the app
app.run()
