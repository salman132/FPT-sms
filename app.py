from fastapi import FastAPI, Form, status, Response
import time, json, requests

app = FastAPI()


def read_json_file(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def write_json_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def get_access_token():
    token_file = "tokens.json"

    data = read_json_file(token_file)

    access_token = data["access_token"]
    expires_in = int(data["expires_in"])
    token_time = data["created_time"]

    if time.time() - token_time > expires_in:
        client_secret = "f96a3527059cc346B84b5b5d960cb21006b41d11587aa4edDa2Cb94142b4c2c7ea0182cc"
        client_id = "c3FcCa19c94547ed9f6c4Ed9eF52180834bf1637"

        url = "https://api01.sms.fpt.net/oauth2/token"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "send_brandname, send_brandname_otp",
            "session_id": "5c22be0c0396440829c98d7ba1240920"
        }

        tokens = requests.post(url, data=json.dumps(data), headers=headers, verify=False).json()
        print(tokens)
        access_token = tokens["access_token"]
        tokens["created_time"] = time.time()

        write_json_file(token_file, tokens)
    return access_token


@app.post("/send/")
async def handle_form(
    phone: str = Form(...), body: str = Form(...), sender: str = Form(...)
):
    try:
        url = "http://app.sms.fpt.net/api/push-brandname-international"
        access_token = get_access_token()
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "access_token": access_token,
            "session_id": "5c22be0c0396440829c98d7ba124092020145753419",
            "BrandName": "FTI",
            "Phone": phone,
            "Message": body,
        }
        return {"msg": "Message sent successfully"}
    except:
        return Response(
            content={"error": "Unable to send msg."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.post("/validate/")
async def validate(generated_otp: str, user_otp: str):
    if generated_otp == user_otp:
        return True
    return False
