# -*- coding: utf-8 -*-

from flask import Flask, url_for, request, render_template, make_response
app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     return 'Hello World!'

@app.route('/')
def index():
    return 'Index Page'

# @app.route('/hello')
# def hello():
#     return 'Hello World'

@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id

@app.route('/projects/')
def projects():
    return 'The project page'

@app.route('/about')
def about():
    return 'The about page'

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         # do_the_login()
#         return 'Do the login'
#     else:
#         # show_the_login_form()
#         return 'The login form'

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'],
                       request.form['password']):
            return log_the_user_in(request.form['username'])
        else:
            error = 'Invalid username/password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template('login.html', error=error)

@app.errorhandler(404)
def not_found(error):
    resp = make_response(render_template('error.html'), 404)
    resp.headers['X-Something'] = 'A value'
    return resp

if __name__ == '__main__':
    # app.debug = True
    # app.run()
    app.run(debug=True)
    # app.run(host='0.0.0.0')