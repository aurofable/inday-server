import os

from flask import Flask
from flask import render_template
from flask import url_for
from flask import request
from flask import jsonify
from flask.ext.sqlalchemy import SQLAlchemy

from twilio import twiml
from twilio.util import TwilioCapability

import string
import random

# Declare and configure application
app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('local_settings.py')
db = SQLAlchemy(app)


# Class for DB
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.String(80), unique=True)
    status = db.Column(db.String(40))
    duration = db.Column(db.Integer)
    recurl = db.Column(db.String(140))
    
    def __init__(self, sid, status, duration, recurl):
        self.sid = sid
        self.status = status
        self.duration = duration
        self.recurl = recurl
    
    def __repr__(self):
        return "('sid', '%s'), ('status', '%s'), ('duration', '%s'), ('recurl','%s')" % (self.sid, self.status, self.duration, self.recurl)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id'        : self.id,
            'sid'       : self.sid,
            'status'    : self.status,
            'duration'  : self.duration,
            'recurl'    : self.recurl
        }



# Voice Request URL
@app.route('/voice', methods=['GET', 'POST'])
def voice():
    caller_id = "+16099526377"
    actionURL = '/trans'
    if request.method == 'GET':
        from_client_number = request.args.get('PhoneNumber')
    else:
        from_client_number = request.form['PhoneNumber']
    response = twiml.Response()
    response.say("Logged In")
    response.dial(action = actionURL, callerId = caller_id, number = from_client_number, record = True)
    print 'Phone number from client is ' + str(from_client_number)
    return str(response)


# SMS Request URL
@app.route('/sms', methods=['GET', 'POST'])
def sms():
    response = twiml.Response()
    response.sms("Congratulations! You deployed the Twilio Hackpack" \
            " for Heroku and Flask.")
    return str(response)


# Twilio Client demo template
@app.route('/client')
def client():
    configuration_error = None
    for key in ('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_APP_SID',
            'TWILIO_CALLER_ID'):
        if not app.config[key]:
            configuration_error = "Missing from local_settings.py: " \
                    "%s" % key
            token = None
    if not configuration_error:
        capability = TwilioCapability(app.config['TWILIO_ACCOUNT_SID'],
            app.config['TWILIO_AUTH_TOKEN'])
        capability.allow_client_incoming("joey_ramone")
        capability.allow_client_outgoing(app.config['TWILIO_APP_SID'])
        token = capability.generate()
    return render_template('client.html', token=token,
            configuration_error=configuration_error)

# Twilio Authentication for iOS Client
@app.route('/auth')
def auth():
    capability = TwilioCapability(app.config['TWILIO_ACCOUNT_SID'],
        app.config['TWILIO_AUTH_TOKEN'])
    capability.allow_client_incoming("swarm_user")
    capability.allow_client_outgoing(app.config['TWILIO_APP_SID'])
    token = capability.generate()
    return str(token)


# Transcription
@app.route('/trans', methods=['GET', 'POST'])
def trans():
    print 'Trans called!'
    if request.method == 'GET':
        recURL = request.args.get('RecordingUrl')
        duration = request.args.get('DialCallDuration')
        sid = request.args.get('DialCallSid')
        status = request.args.get('DialCallStatus')
    else:
        recURL = request.form['RecordingUrl']
        duration = request.form['DialCallDuration']
        sid = request.form['DialCallSid']
        status = request.form['DialCallStatus']
    
    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    if (recURL == None): 
        recURL = "asdfsadfadsf"
    if (duration == None):
        duration = 5
    if (sid == None):
        sid = ''.join(random.choice(chars) for x in range(10))
    if (status == None):
        status = "Error"
    
    note = Note(sid, status, duration, recURL)
    db.session.add(note)
    db.session.commit()

    response = twiml.Response()
    response.say("Recorded")
    return str(response)
   
# Database
@app.route('/data', methods=['GET', 'POST'])
def data():
    if (len(Note.query.all()) == 0):
        return 'Database empty'
    return jsonify(values=[i.serialize for i in Note.query.all()])

# Clear Database
@app.route('/clear', methods=['GET', 'POST'])
def clear():
   for note in Note.query.all():
       db.session.delete(note)
   db.session.commit()
   return 'Databse Cleared'

# Index page
@app.route('/')
def index():
    params = {
        'voice_request_url': url_for('.voice', _external=True),
        'client_url': url_for('.client', _external=True),
        'auth_url': url_for('.auth', _external=True),
        'trans_url': url_for('.trans', _external=True),
        'data_url' : url_for('.data', _external=True)}
    return render_template('index.html', params=params)


# If PORT not specified by environment, assume development config.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)
    db.create_all()
