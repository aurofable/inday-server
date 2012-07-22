import os

from flask import Flask
from flask import render_template
from flask import url_for
from flask import request

from twilio import twiml
from twilio.util import TwilioCapability


# Declare and configure application
app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('local_settings.py')


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
    print str(response)
    print '\n'
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
    else:
        recURL = request.form['RecordingUrl']
    print recURL
    response = twiml.Response()
    response.say("Transcribing")
    return str(response)
    




# Index page
@app.route('/')
def index():
    params = {
        'voice_request_url': url_for('.voice', _external=True),
        'sms_request_url': url_for('.sms', _external=True),
        'client_url': url_for('.client', _external=True),
        'auth_url': url_for('.auth', _external=True),
        'trans_url': url_for('.trans', _external=True)}
    return render_template('index.html', params=params)


# If PORT not specified by environment, assume development config.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)
