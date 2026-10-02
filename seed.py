from datetime import datetime, timedelta, timezone
import math, random, secrets
from sqlalchemy import delete, select
from app.db.session import Base, SessionLocal, engine
from app.models import Province, District, GridSubstation, SolarInstallation, GenerationReading, User
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

PROVINCES = [
    "Western", "Central", "Southern", "Northern", "Eastern",
    "North Western", "North Central", "Uva", "Sabaragamuwa"
]

DISTRICTS = [
    ("Colombo","Western"),("Gampaha","Western"),("Kalutara","Western"),
    ("Kandy","Central"),("Matale","Central"),("Nuwara Eliya","Central"),
    ("Galle","Southern"),("Matara","Southern"),("Hambantota","Southern"),
    ("Jaffna","Northern"),("Kilinochchi","Northern"),("Mannar","Northern"),
    ("Vavuniya","Northern"),("Mullaitivu","Northern"),
    ("Batticaloa","Eastern"),("Ampara","Eastern"),("Trincomalee","Eastern"),
    ("Kurunegala","North Western"),("Puttalam","North Western"),
    ("Anuradhapura","North Central"),("Polonnaruwa","North Central"),
    ("Badulla","Uva"),("Monaragala","Uva"),
    ("Ratnapura","Sabaragamuwa"),("Kegalle","Sabaragamuwa")
]

def run():
    db = SessionLocal()
    try:
        # Reset only the coursework database.
        for model in [GenerationReading, User, SolarInstallation, GridSubstation, District, Province]:
            db.execute(delete(model))
        db.commit()

        provinces = {}
        for name in PROVINCES:
            p = Province(name=name)
            db.add(p); db.flush()
            provinces[name] = p

        districts = {}
        for name, province_name in DISTRICTS:
            d = District(name=name, province_id=provinces[province_name].id)
            db.add(d); db.flush()
            districts[name] = d

        substations = []
        for i in range(20):
            district = list(districts.values())[i % len(districts)]
            s = GridSubstation(name=f"GS-{i+1:03d}", district_id=district.id)
            db.add(s); db.flush()
            substations.append(s)

        installations = []
        for i in range(200):
            s = substations[i % len(substations)]
            inst = SolarInstallation(
                site_name=f"Solar Site {i+1:03d}",
                meter_id=f"SLSEA-MTR-{i+1:05d}",
                capacity_kw=round(random.uniform(3.0, 25.0), 2),
                address=f"{s.district.name} Solar Site {i+1:03d}",
                substation_id=s.id,
            )
            db.add(inst); db.flush()
            installations.append(inst)

        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for inst in installations:
            cumulative = 0.0
            for step in range(7 * 24):  # one week, hourly seed data
                ts = now - timedelta(hours=(7 * 24 - 1 - step))
                hour = ts.hour
                daylight = max(0.0, math.sin(math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0.0
                power = round(inst.capacity_kw * daylight * random.uniform(0.75, 1.05), 3)
                cumulative += power
                db.add(GenerationReading(
                    installation_id=inst.id,
                    timestamp=ts,
                    power_kw=power,
                    cumulative_energy_kwh=round(cumulative, 3),
                    voltage=round(random.uniform(220, 240), 2),
                    created_at=ts,
                ))

        # Demo credentials. Change/remove before final public use.
        national = User(username="national_analyst", password_hash=hash_password("NationalDemo123!"), role="national_analyst")
        db.add(national)
        first_district = list(districts.values())[0]
        district_user = User(username="district_analyst", password_hash=hash_password("DistrictDemo123!"), role="district_analyst", district_id=first_district.id)
        db.add(district_user)
        device_user = User(username="device_001", password_hash=hash_password("DeviceDemo123!"), role="device", installation_id=installations[0].id)
        db.add(device_user)
        db.commit()
        print("Seed complete: 9 provinces, 25 districts, 20 substations, 200 installations, 33,600 readings.")
        print("Demo users: national_analyst / NationalDemo123!, district_analyst / DistrictDemo123!, device_001 / DeviceDemo123!")
    finally:
        db.close()

if __name__ == "__main__":
    run()
