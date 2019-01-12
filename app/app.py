import os
import uuid
import subprocess

from flask import Flask, jsonify, request, abort, send_file, after_this_request

app = Flask(__name__, static_folder=None)

_dirname = os.path.dirname(__file__)
app.config['DIRECTORIES'] = {
    'upload': os.path.join(_dirname, '..', 'posted_images'),
    'results': os.path.join(_dirname, '..', 'results'),
    'FaceSwap': os.path.join(_dirname, '..', 'FaceSwap')
}

for directory in app.config['DIRECTORIES'].values():
    if not os.path.exists(directory):
        os.makedirs(directory)


def format_error(func):
    def wrapper(*args, **kwargs):
        err, code = func(*args, **kwargs)

        return jsonify({'error': {'message': err.description, 'code': code}}), code

    return wrapper


@app.errorhandler(400)
@format_error
def bad_request(err):
    return err, 400


@app.errorhandler(404)
@format_error
def not_found(err):
    return err, 404


@app.errorhandler(405)
@format_error
def method_not_allowed(err):
    return err, 405


@app.route('/swap', methods=['POST'])
def swap():
    required_fields = ('src', 'dst')

    missing_field = next((field for field in required_fields if field not in request.files), None)

    if missing_field:
        abort(400, 'Missing required file with key: {}'.format(missing_field))

    not_selected_file = next((field for field in required_fields if request.files[field].filename == ''), None)

    if not_selected_file:
        abort(400, 'Not selected {} file'.format(not_selected_file))

    return face_swap(*[request.files[field] for field in required_fields])


def face_swap(src, dst):
    # save both files
    files = [save_file(file) for file in (src, dst)]
    result_img = os.path.join(app.config['DIRECTORIES']['results'], str(uuid.uuid4()) + '.jpg')
    files.append(result_img)

    @after_this_request
    def cleanup(response):
        for f in files:
            if os.path.exists(f):
                os.remove(f)
        return response

    # execute face swap in subprocess
    cmd = get_command(*files)
    print('cmd: {}'.format(' '.join(cmd)))
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=app.config['DIRECTORIES']['FaceSwap']
    )

    stdout, stderr = proc.communicate()

    if stderr:
        abort(400, stderr.decode())

    return send_file(result_img, mimetype='image/jpeg')


def save_file(file):
    filename = os.path.join(app.config['DIRECTORIES']['upload'], file.filename)
    file.save(filename)

    return filename


def get_command(src, dst, result):
    return ['python3', 'main.py', '--src', src, '--dst', dst, '--out', result, '--no_debug_window']


def main():
    app.run(port=1234, debug=True)


if __name__ == '__main__':
    main()
