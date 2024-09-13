from fastapi import FastAPI, status, Response
from pydantic import BaseModel
import time, json, requests, base64

app = FastAPI()


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


@app.post("/send/")
async def handle_form(data: DataModel):
    try:
        bytes_string = data.body.encode("utf-8")
        base64_encoded = base64.b64encode(bytes_string).decode("utf-8")
        url = "http://api01.sms.fpt.net/api/push-brandname-otp"
        access_token = get_access_token()

        if (
            access_token == "No token data available"
            or "Failed to get access token" in access_token
        ):
            return Response(
                content=json.dumps({"error": access_token}),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                media_type="application/json",
            )

        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "access_token": access_token,
            "session_id": "5c22be0c0396440829c98d7ba124092020145753419",
            "BrandName": "ARROWSTER",
            "Phone": data.phone,
            "Message": base64_encoded,
        }
        resp = requests.post(url, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error handling form: {e}")
        return Response(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
