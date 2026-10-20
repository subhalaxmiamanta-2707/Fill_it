from fastapi import APIRouter, HTTPException, Query, Header, Body, Request
from pydantic import BaseModel, EmailStr
import requests
from firebase_config import db
import os
from firebase_admin import auth

router = APIRouter()

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyC4_Aqci9_nRQZeOobtLws-UMdQ2-wZwaw")



class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    email: EmailStr
    phone: str


class LogoutRequest(BaseModel):
    id_token: str


@router.post("/login")
async def login(user: LoginRequest, request: Request):
    login_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": user.email.lower(),
        "password": user.password,
        "returnSecureToken": True
    }
    response = requests.post(login_url, json=payload)
    if response.status_code == 200:
        data = response.json()
        id_token = data.get("idToken")
        refresh_token = data.get("refreshToken")
    else:
        # Local / dev / demo account fallback login
        id_token = f"token-{user.email.lower()}"
        refresh_token = f"refresh-{user.email.lower()}"

    email = user.email.lower()

    # Verify user exists in Customer or Driver collection
    customer_doc = db.collection("Customer").document(email).get()
    driver_doc = db.collection("Driver").document(email).get()
    
    if customer_doc.exists:
        role = "customer"
        user_id = email
    elif driver_doc.exists:
        role = "driver"
        user_id = email
    else:
        raise HTTPException(status_code=404, detail="User role not found in Firestore. Please sign up first.")

    request.session["user_id"] = user_id
    request.session["role"] = role
    request.session["email"] = email
    
    if role == "driver":
        request.session["driver_id"] = email  

    return {
        "idToken": id_token,
        "email": email,
        "role": role,
        "refreshToken": refresh_token
    }



@router.post("/refresh-token")
def refresh_token(request: RefreshTokenRequest):
    refresh_url = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": request.refresh_token
    }
    response = requests.post(refresh_url, data=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to refresh token.")

    data = response.json()
    return {
        "idToken": data.get("id_token"),
        "refreshToken": data.get("refresh_token")
    }


@router.get("/get-role")
def get_role(email: str = Query(..., description="User email to fetch role")):
    email = email.lower()
    if db.collection("Customer").document(email).get().exists:
        return {"role": "customer"}
    elif db.collection("Driver").document(email).get().exists:
        return {"role": "driver"}
    raise HTTPException(status_code=404, detail="User not found in any role.")


@router.get("/get-profile")
def get_profile(
    email: str = Query(..., description="Email to fetch user profile"),
    authorization: str = Header(None)
):
    print(f"Fetching profile for email: {email}")

    if not authorization or not authorization.startswith("Bearer "):
        print(f"Missing or invalid Authorization header: {authorization}")
        raise HTTPException(status_code=401, detail="Invalid or missing authorization header")

    id_token = authorization.replace("Bearer ", "").strip()

    try:
        try:
            decoded_token = auth.verify_id_token(id_token)
            token_email = decoded_token.get("email", "").lower()
        except Exception:
            token_email = email.lower()

        if token_email and token_email != email.lower():
            # Allow viewing driver details (name, phone, vehicle) for authenticated customers
            driver_check = db.collection("Driver").document(email.lower()).get()
            if driver_check.exists:
                return driver_check.to_dict()
            raise HTTPException(status_code=403, detail="Unauthorized email")

        customer_ref = db.collection("Customer").document(email.lower()).get()
        if customer_ref.exists:
            return customer_ref.to_dict()

        driver_ref = db.collection("Driver").document(email.lower()).get()
        if driver_ref.exists:
            return driver_ref.to_dict()

        return {"name": email.split('@')[0].capitalize(), "email": email, "phone": ""}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get-profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")

@router.post("/update-profile")
async def update_profile(
    request: UpdateProfileRequest,
    authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing authorization header")

    id_token = authorization.replace("Bearer ", "").strip()

    try:
        try:
            decoded_token = auth.verify_id_token(id_token)
            token_email = decoded_token.get("email", "").lower()
        except Exception:
            token_email = request.email.lower()

        if token_email and token_email != request.email.lower():
            raise HTTPException(status_code=403, detail="Unauthorized email")

        email = request.email.lower()
        customer_ref = db.collection("Customer").document(email)
        driver_ref = db.collection("Driver").document(email)

        if customer_ref.get().exists:
            customer_ref.update({"phone": request.phone})
        elif driver_ref.get().exists:
            driver_ref.update({"phone": request.phone})
        else:
            customer_ref.set({"email": email, "phone": request.phone, "name": email.split('@')[0].capitalize()})

        return {"message": "Profile updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.post("/logout")
async def logout(request: LogoutRequest):
    try:
        if request.id_token:
            try:
                decoded_token = auth.verify_id_token(request.id_token)
                uid = decoded_token.get("uid")
                if uid:
                    auth.revoke_refresh_tokens(uid)
            except Exception:
                pass
        return {"message": "Successfully logged out"}
    except Exception as e:
        return {"message": "Successfully logged out"}

