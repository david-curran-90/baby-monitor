from flask import Flask, render_template, Response, request
from . import camera
from . import audio

app = Flask(__name__)        

# will fail as there's no index.html
@app.route('/')
def index():
    return render_template('index.html')

# returns a still image from the camera
def gen_video(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video')
def video_feed():
    return Response(gen_video(camera.VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_audio(audio):
    first_run = True
    sound = audio.stream()
    while True:
        if first_run:
            data = audio.gen_header() + sound.read(74)
        else:
            data = sound.read(74)
    yield(data)

@app.route('/audio')
def audio_feed():
    return Response(gen_audio(audio.Audio(channels=1, rlength=60)))

# nice secure method for shutdown
@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return('server shutting down')
    
def run():
    app.run(host='0.0.0.0', debug=False)

if __name__ == '__main__':
    run()