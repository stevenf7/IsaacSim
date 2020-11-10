import requests


def setup():
    comm = KitCommunication()
    return comm


class KitCommunication(object):
    def __init__(self, url="127.0.0.1", port="8080"):
        self._address = "http://" + url + ":" + port

    def post_command(self, request_dict):
        try:
            # print("POST_COMMAND Trying: ", request_dict)
            resp = requests.post(self._address, json=request_dict)
            # print ("POST_COMMAND Response: ", resp.status_code)
            if resp.status_code != requests.codes.ok:
                raise KitEngineException(resp.status_code, resp.json())
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise KitCommunicationException(str(e))


class KitEngineException(Exception):
    def __init__(self, status_code, resp_dict):
        resp_msg = resp_dict["message"] if "message" in resp_dict else "Message not available"
        self.message = f"Kit returned response with status: {status_code} ({requests.status_codes._codes[status_code][0]}), message: {resp_msg}"


class KitCommunicationException(Exception):
    def __init__(self, message):
        self.message = message


def test_comm():
    comm = setup()
    command = {}
    command["synsetId"] = "02691156"
    command["modelId"] = "dd9ece07d4bc696c2bafe808edd44356"
    command["pos"] = (10.0, 11.0, 12.0)  # optional
    command["rot"] = ((0.0, 0.0, 1.0), 90.0)  # optional
    command["scale"] = 1.1  # optional

    print(command)

    comm.post_command(command)
