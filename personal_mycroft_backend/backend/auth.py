from personal_mycroft_backend.backend import app, API_VERSION, DEVICES
from personal_mycroft_backend.backend.utils import nice_json, gen_api
from personal_mycroft_backend.backend.decorators import noindex, donation, requires_admin
from personal_mycroft_backend.database import model_to_dict

from flask import request, Response
import time


@app.route("/" + API_VERSION + "/pair/<code>/<uuid>/<name>/<mail>",
           methods=['PUT'])
@noindex
@donation
@requires_admin
def pair(code, uuid, name, mail):
    # pair
    result = {"paired": False}
    device = DEVICES.get_unpaired_by_uuid(uuid)
    if device and device.code == code:
        user = DEVICES.get_user_by_mail(mail)
        # create user if it doesnt exist
        if not user:
            DEVICES.add_user(mail, name, "666")
        if DEVICES.add_device(uuid, mail=mail):
            DEVICES.remove_unpaired(uuid)
            result = {"paired": True}
    return nice_json(result)


@app.route("/"+API_VERSION+"/auth/token", methods=['GET'])
@noindex
@donation
def token():
    api = request.headers.get('Authorization', '').replace("Bearer ", "")
    device = DEVICES.get_device_by_token(api)
    if not device:
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to authenticate with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="NOT PAIRED"'})
    # token to refresh expired token
    if device.refreshToken is None or device.refreshToken != api:
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to authenticate with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="BAD REFRESH CODE"'})
    # new tokens to access
    access_token = gen_api()
    new_refresh_token = gen_api()

    DEVICES.add_device(uuid=device.uuid, expires_at=time.time() + 72000,
                       accessToken=access_token,
                       refreshToken=new_refresh_token)

    return nice_json(model_to_dict(device))
