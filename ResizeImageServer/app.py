import os
from flask import Flask, request, render_template, send_from_directory
import json
from PIL import Image
import requests
import socket
app = Flask(__name__)


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DIR_PATH = 'images'

PORT = 80
MY_IP = socket.gethostbyname(socket.gethostname())
PROTOCOL = 'http'

LOCAL = '{}://{}:{}'.format(PROTOCOL, MY_IP, PORT)


def thumbnail_maker(img):
    r = requests.get(img)
    path = '/'.join([APP_ROOT, DIR_PATH, 'thumb.jpg'])
    with open(path, 'wb') as f:
        f.write(r.content)
    image = Image.open(path)
    image.thumbnail((200, 200))

    image.save(path)

    return '/'.join([LOCAL, 'upload', 'thumb.jpg'])


def detail_resizing(img):
    r = requests.get(img)
    path = '/'.join([APP_ROOT, DIR_PATH, 'detail.jpg'])
    with open(path, 'wb') as f:
        f.write(r.content)
    image = Image.open(path)

    image = image.resize((758, 1500))

    image.save(path)

    return '/'.join([LOCAL, 'upload', 'detail.jpg'])


def detail_cropping(img):
    r = requests.get(img)
    path = '/'.join([APP_ROOT, DIR_PATH, 'detail.jpg'])
    with open(path, 'wb') as f:
        f.write(r.content)
    image = Image.open(path)
    split_set = int(image.size[1] / 1500) + 1

    point, details = 0, []
    for n in range(split_set):
        file_ = 'detail_{}.jpg'.format(n)
        details.append('/'.join([LOCAL, 'upload', file_]))

        width, height = image.size
        left, top, right, bottom = 0, point, width, point + 1500

        if bottom > height:
            bottom = height

        image.crop((left, top, right, bottom)).save('/'.join([APP_ROOT, DIR_PATH, file_]))

        point += 1500

    return details


@app.route('/upload', methods=['POST'])
def upload():
    target = os.path.join(APP_ROOT, DIR_PATH)
    if not os.path.isdir(target):
        os.mkdir(target)

    if request.method == 'POST':
        res = json.loads(request.get_data().decode())
        # res['image_path'], res['type_']
        if not res:
            return json.dumps({'suc': False, 'data': '', 'msg': 'need to json data image_path, type_'})

        if res['type_'] == 'thumb':
            save = thumbnail_maker(res['image_path'])
            return json.dumps({'suc': True, 'data': '/'.join([LOCAL, 'upload', save]), 'msg': ''})

        elif res['type_'] == 'detail':
            save = detail_cropping(res['image_path'])
            return json.dumps({'suc': True, 'data': save, 'msg': ''})

        else:
            return json.dumps({'suc': False, 'data': '', 'msg': 'invalid type. select thumb or detail'})

    else:
        return json.dumps({'suc': False, 'data': '', 'msg': 'invalid method.'})


@app.route('/upload/<filename>', methods=['GET', 'POST'])
def send_to_gallery(filename):
    return send_from_directory('images', filename)


@app.route('/gallery', methods=['GET'])
def gallery():
    return render_template('gallery.html', image_names=os.listdir('/'.join([APP_ROOT, DIR_PATH])))


app.run(port=PORT, host='0.0.0.0')



