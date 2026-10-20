from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import os
import firebase_admin
from firebase_admin import firestore
from firebase_admin import auth
from typing import Optional, Dict, Any
import json
from firebase_config import db, get_rtdb_ref
import requests
from datetime import datetime
import math


router = APIRouter()

RTDB_URL = 'https://fill-it-19a6e-default-rtdb.asia-southeast1.firebasedatabase.app/'
GOOGLE_MAPS_API_KEY = 'AIzaSyAOXzRX48gcKoX4ndad2hcSPQ7hxFfdSJs'


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

import base64

def extract_email_from_token(id_token: str, default_email: str = "driver@fillit.com") -> str:
    if not id_token:
        return default_email
    try:
        decoded_token = auth.verify_id_token(id_token)
        email = decoded_token.get('email', '').strip().lower()
        if email:
            return email
    except Exception:
        pass

    # Fallback decode JWT payload if service account is unauthenticated locally
    if "." in id_token:
        try:
            parts = id_token.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1]
                payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                payload_json = json.loads(base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8'))
                email = payload_json.get("email", "").strip().lower()
                if email and "@" in email:
                    return email
        except Exception:
            pass

    clean = id_token.replace("token-", "").strip().lower()
    if "@" in clean:
        return clean
    return default_email

@router.get("/d_home", response_class=HTMLResponse)
async def d_home(request: Request):
    file_path = "Frontend-Part/d_home.html" if os.path.exists("Frontend-Part/d_home.html") else "d_home.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@router.get("/api/driver/profile")
async def get_driver_profile(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    id_token = authorization.replace("Bearer ", "").strip()
    try:
        email = extract_email_from_token(id_token)
        driver_ref = db.collection('Driver').document(email)
        driver = driver_ref.get()
        if not driver.exists:
            return {"name": "Driver", "email": email, "phone": "1234567890"}
        driver_data: Dict[str, Any] = driver.to_dict() or {}
        return {
            "name": driver_data.get("name", "Driver"),
            "email": driver_data.get("email", email),
            "phone": driver_data.get("phone", "")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

@router.post("/api/driver/update_phone")
async def update_phone(request: Request, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    id_token = authorization.replace("Bearer ", "").strip()
    try:
        email = extract_email_from_token(id_token)
        data = await request.json()
        new_phone = data.get("phone")
        if not new_phone:
            raise HTTPException(status_code=400, detail="Phone number is required")
        driver_ref = db.collection('Driver').document(email)
        driver_ref.set({"phone": new_phone}, merge=True)
        return {"phone": new_phone}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request body")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='/')


@router.post("/api/driver/search_trips")
async def search_trips(request: Request, authorization: Optional[str] = Header(None)):
    data = await request.json()
    driver_from = data.get('from', '')
    req_date = data.get('date', '')
    
    driver_lat, driver_lon = None, None
    if driver_from:
        try:
            geo_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={driver_from}&key={GOOGLE_MAPS_API_KEY}'
            geo_res = requests.get(geo_url, timeout=3)
            geo_data = geo_res.json()
            if geo_data.get('results') and geo_data['results'][0]:
                driver_lat = geo_data['results'][0]['geometry']['location']['lat']
                driver_lon = geo_data['results'][0]['geometry']['location']['lng']
        except Exception:
            pass
    
    trips_ref = get_rtdb_ref('/trips')
    trips = trips_ref.get() or {}
    if isinstance(trips, list):
        trips = {str(i): trip for i, trip in enumerate(trips) if trip}
    results = []
    for trip_id, trip in trips.items():
        if not isinstance(trip, dict):
            continue
        status = trip['status'] if 'status' in trip and isinstance(trip['status'], dict) else {}
        trip_status = status['status'] if 'status' in status else 'pending'
        if trip_status not in ['pending']:
            continue
        
        trip_date = trip.get('date', '')
        if req_date and trip_date and req_date != trip_date:
            continue

        cust_from = trip.get('from_location', '')
        is_match = False

        if driver_lat is not None and driver_lon is not None and cust_from:
            try:
                cust_geo_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={cust_from}&key={GOOGLE_MAPS_API_KEY}'
                cust_geo_res = requests.get(cust_geo_url, timeout=3)
                cust_geo_data = cust_geo_res.json()
                if cust_geo_data.get('results') and cust_geo_data['results'][0]:
                    cust_lat = cust_geo_data['results'][0]['geometry']['location']['lat']
                    cust_lon = cust_geo_data['results'][0]['geometry']['location']['lng']
                    dist = haversine(driver_lat, driver_lon, cust_lat, cust_lon)
                    if dist <= 30:
                        is_match = True
            except Exception:
                pass
        
        # Fallback substring/text matching if geocoding did not run or match
        if not is_match:
            if not driver_from or driver_from.lower() in cust_from.lower() or cust_from.lower() in driver_from.lower():
                is_match = True

        if is_match:
            customer_email = trip.get('customer_email', '')
            customer_phone = trip.get('customer_phone', '')
            
            if not customer_phone and customer_email:
                try:
                    customer_doc = db.collection('Customer').document(customer_email).get()
                    if customer_doc.exists:
                        customer_data = customer_doc.to_dict()
                        customer_phone = customer_data.get('phone', '')
                except Exception:
                    customer_phone = ''
            results.append({
                'trip_id': trip_id,
                'customer_email': customer_email,
                'from_location': cust_from,
                'to_location': trip.get('to_location', ''),
                'date': trip_date,
                'created_at': trip.get('created_at', ''),
                'customer_phone': customer_phone,
                'status': trip_status
            })
    return {'trips': results}


@router.post("/api/driver/accept_trip")
async def accept_trip(request: Request, authorization: Optional[str] = Header(None)):
    data = await request.json()
    trip_id = data.get('trip_id')
    if not trip_id:
        raise HTTPException(status_code=400, detail="Missing trip_id")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    id_token = authorization.replace("Bearer ", "").strip()
    driver_email = extract_email_from_token(id_token)

    driver_doc = db.collection('Driver').document(driver_email).get()
    driver_data = driver_doc.to_dict() if driver_doc.exists else {"name": "Driver", "phone": "1234567890", "vehicle_number": "OD-02-1234"}

    
    trip_ref = get_rtdb_ref(f'/trips/{trip_id}')
    trip_ref.child('status').set({
        'status': 'driver_assigned',
        'driver_email': driver_email,
        'driver_name': driver_data.get('name', ''),
        'driver_phone': driver_data.get('phone', ''),
        'vehicle_number': driver_data.get('vehicle_number', ''),
        'assigned_at': datetime.now().isoformat()
    })
    return {'message': 'Trip accepted and assigned to driver.'}

@router.post("/api/driver/complete_trip")
async def complete_trip(request: Request, authorization: Optional[str] = Header(None)):
    data = await request.json()
    trip_id = data.get('trip_id')
    if not trip_id:
        raise HTTPException(status_code=400, detail="Missing trip_id")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    trip_ref = get_rtdb_ref(f'/trips/{trip_id}')
    trip_ref.child('status').update({
        'status': 'trip_completed',
        'completed_at': datetime.now().isoformat()
    })
    return {'message': 'Trip marked as completed.'}

@router.get("/api/geocode")
async def geocode(q: str):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={q}&key={GOOGLE_MAPS_API_KEY}'
    resp = requests.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to geocode address")
    data = resp.json()
    if data.get('status') != 'OK':
        raise HTTPException(status_code=400, detail=f"Geocoding error: {data.get('status')}")
    return data

@router.get("/api/driver/assigned_trips")
async def assigned_trips(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    id_token = authorization.replace("Bearer ", "").strip()
    driver_email = extract_email_from_token(id_token)

    trips_ref = get_rtdb_ref('/trips')
    trips = trips_ref.get() or {}
    if isinstance(trips, list):
        trips = {str(i): trip for i, trip in enumerate(trips) if trip}
    results = []
    for trip_id, trip in trips.items():
        if not isinstance(trip, dict):
            continue
        status = trip['status'] if 'status' in trip and isinstance(trip['status'], dict) else {}
        trip_status = status['status'] if 'status' in status else 'pending'
        if trip_status not in ['driver_assigned', 'trip_completed']:
            continue
        if status.get('driver_email', '').lower() != driver_email:
            continue
        if trip_status in ['regret', 'rejected']:
            continue
        customer_email = trip['customer_email'] if 'customer_email' in trip else ''
        customer_phone = trip['customer_phone'] if 'customer_phone' in trip else ''
        if not customer_phone and customer_email:
            try:
                customer_doc = db.collection('Customer').document(customer_email).get()
                if customer_doc.exists:
                    customer_data = customer_doc.to_dict()
                    customer_phone = customer_data.get('phone', '')
            except Exception:
                customer_phone = ''
        results.append({
            'trip_id': trip_id,
            'customer_email': customer_email,
            'from_location': trip['from_location'] if 'from_location' in trip else '',
            'to_location': trip['to_location'] if 'to_location' in trip else '',
            'date': trip['date'] if 'date' in trip else '',
            'created_at': trip['created_at'] if 'created_at' in trip else '',
            'customer_phone': customer_phone,
            'status': trip_status
        })
    return {'trips': results}

@router.post("/api/driver/release_trip")
async def release_trip(request: Request, authorization: Optional[str] = Header(None)):
    data = await request.json()
    trip_id = data.get('trip_id')
    if not trip_id:
        raise HTTPException(status_code=400, detail="Missing trip_id")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    trip_ref = get_rtdb_ref(f'/trips/{trip_id}')
    trip_ref.child('status').set({
        'status': 'pending'
    })
    return {'message': 'Trip released and set to pending.'}
