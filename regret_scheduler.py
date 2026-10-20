from apscheduler.schedulers.background import BackgroundScheduler
from firebase_config import get_rtdb_ref

from datetime import datetime
import pytz


def update_pending_to_regret():
    try:
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).date()
        trips_ref = get_rtdb_ref('/trips')

        all_trips = trips_ref.get()
        if not all_trips:
            return
        if isinstance(all_trips, list):
            all_trips = {str(i): trip for i, trip in enumerate(all_trips) if trip}
        for trip_id, trip in all_trips.items():
            if not isinstance(trip, dict):
                continue
            status_val = trip.get('status')
            if isinstance(status_val, dict):
                status = status_val.get('status')
            elif isinstance(status_val, str):
                status = status_val
            else:
                status = None
            booking_date = trip.get('date')
            if status == 'pending' and booking_date:
                booking_date_obj = None
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                    try:
                        booking_date_obj = datetime.strptime(booking_date, fmt).date()
                        break
                    except ValueError:
                        continue
                if booking_date_obj and booking_date_obj < today:
                    trips_ref.child(trip_id).child('status').update({
                        'status': 'regret',
                        'updated_at': datetime.now(ist).isoformat()
                    })
    except Exception as e:
        print(f"Regret scheduler error: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(update_pending_to_regret, 'interval', hours=1)  
scheduler.start() 
