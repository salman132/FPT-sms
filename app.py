from fastapi import FastAPI, status, Response
from pydantic import BaseModel
import time, json, requests, base64
from services import log_message

from fastapi import FastAPI, Form, status, Response
from twilio.rest import Client
import config

app = FastAPI()
settings = config.Settings()


class DataModel(BaseModel):
    phone: str
    body: str


def read_json_file(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_access_token() -> str:
    token_file = "tokens.json"

    data = read_json_file(token_file)

    access_token = data["access_token"]
    expires_in = int(data["expires_in"])
    token_time = data["created_time"]

    if time.time() - token_time > expires_in:
        client_secret = (
            "f96a3527059cc346B84b5b5d960cb21006b41d11587aa4edDa2Cb94142b4c2c7ea0182cc"
        )
        client_id = "c3FcCa19c94547ed9f6c4Ed9eF52180834bf1637"

        url = "https://api01.sms.fpt.net/oauth2/token"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "send_brandname_otp",
            "session_id": "5c22be0c0396440829c98d7ba1240920",
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()  # Raise an error for bad HTTP responses
            tokens = response.json()
        except requests.RequestException as e:
            print(f"Error getting access token: {e}")
            return f"Failed to get access token: {e}"

        access_token = tokens.get("access_token", "")
        tokens["created_time"] = time.time()
        with open(token_file, "w") as file:
            json.dump(tokens, file, indent=4)

    return access_token


@app.post("/vn/send/")
async def handle_form(data: DataModel):
    try:
        bytes_string = data.body.encode("utf-8")
        base64_encoded = base64.b64encode(bytes_string).decode("utf-8")
        url = "http://api01.sms.fpt.net/api/push-brandname-otp"
        access_token = get_access_token()

        log_message("info", f"Access token: {access_token}")

        if (
            access_token == "No token data available"
            or "Failed to get access token" in access_token
        ):
            return Response(
                content=json.dumps({"error": access_token}),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                media_type="application/json",
            )

        headers = {"Content-Type": "application/json"}
        data_payload = {
            "access_token": access_token,
            "session_id": "5c22be0c0396440829c98d7ba124092020145753419",
            "BrandName": "ARROWSTER",
            "Phone": data.phone.replace("+84", ""),
            "Message": base64_encoded,
        }

        log_message("info", f"Data payload: {json.dumps(data_payload, indent=4)}")

        resp = requests.post(url, json=data_payload, headers=headers)
        resp.raise_for_status()

        log_message("info", f"Response: {resp.json()}")
        return resp.json()
    except requests.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        log_message("error", f"Request failed: {error_message}")
        return Response(
            content=json.dumps({"error": error_message}),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json",
        )
    except Exception as e:
        log_message("error", f"Unhandled exception: {str(e)}")
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json",
        )


@app.post("/send/")
async def handle_form(
    phone: str = Form(...), body: str = Form(...), sender: str = Form(...)
):
    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.region = "us1"
        client.messages.create(to=phone, from_=settings.twilio_phone_number, body=body)
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
