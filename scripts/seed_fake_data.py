from __future__ import annotations

import base64
import random
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import settings
from app.db.models import (
    AccessAudit,
    Client,
    Image,
    IngestionLog,
    Patient,
    QCTFollowup,
    QCTNodule,
    QCTSummary,
    Series,
    Site,
    Study,
    User,
)
from app.db.session import SessionLocal

IMAGE_DIR = Path("images/mock_ct")

SVG_BYTES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">\n'
    "  <defs>\n"
    '    <radialGradient id="ct_bg" cx="50%" cy="50%" r="60%">\n'
    '      <stop offset="0%" stop-color="#7a8088"/>\n'
    '      <stop offset="45%" stop-color="#4d545d"/>\n'
    '      <stop offset="100%" stop-color="#1e242a"/>\n'
    "    </radialGradient>\n"
    '    <filter id="grain" x="-10%" y="-10%" width="120%" height="120%">\n'
    '      <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" seed="11"/>\n'
    '      <feColorMatrix type="saturate" values="0"/>\n'
    '      <feComponentTransfer>\n'
    '        <feFuncA type="table" tableValues="0 0.22"/>\n'
    "      </feComponentTransfer>\n"
    "    </filter>\n"
    '    <filter id="soft_blur" x="-20%" y="-20%" width="140%" height="140%">\n'
    '      <feGaussianBlur stdDeviation="3"/>\n'
    "    </filter>\n"
    "  </defs>\n"
    '  <rect width="1200" height="800" fill="#e7ebe8"/>\n'
    '  <rect x="70" y="90" width="1060" height="620" rx="28" fill="#d2dad6"/>\n'
    '  <g transform="translate(600 400)">\n'
    '    <circle r="300" fill="url(#ct_bg)"/>\n'
    '    <circle r="270" fill="#2b3037"/>\n'
    '    <circle r="285" fill="none" stroke="#a5adb6" stroke-opacity="0.25" stroke-width="2"/>\n'
    '    <circle r="255" fill="none" stroke="#a5adb6" stroke-opacity="0.18" stroke-width="2"/>\n'
    '    <circle r="230" fill="none" stroke="#a5adb6" stroke-opacity="0.12" stroke-width="2"/>\n'
    '    <ellipse cx="-105" cy="-8" rx="120" ry="175" fill="#1c2025"/>\n'
    '    <ellipse cx="105" cy="-8" rx="120" ry="175" fill="#1c2025"/>\n'
    '    <ellipse cx="0" cy="85" rx="45" ry="80" fill="#262b31"/>\n'
    '    <circle cx="-60" cy="-45" r="26" fill="#6b737c"/>\n'
    '    <circle cx="75" cy="5" r="20" fill="#707880"/>\n'
    '    <circle cx="20" cy="-95" r="14" fill="#616970"/>\n'
    '    <circle r="260" fill="#000" opacity="0.18" filter="url(#grain)"/>\n'
    '    <circle r="210" fill="none" stroke="#c1c7cf" stroke-opacity="0.08" stroke-width="6" '
    'filter="url(#soft_blur)"/>\n'
    "  </g>\n"
    '  <text x="600" y="720" font-family="Arial, sans-serif" font-size="28" '
    'fill="#7a838b" text-anchor="middle">Simulated CT preview</text>\n'
    "</svg>\n"
).encode("utf-8")

RISK_LEVELS = ["low", "medium", "high"]
STATUS_LEVELS = ["ready", "processing", "review"]
LOCATIONS = ["RUL", "RML", "RLL", "LUL", "LLL"]


def diameter_from_volume(volume_mm3: float) -> float:
    radius = ((3 * volume_mm3) / (4 * 3.14159)) ** (1 / 3)
    return radius * 2


def risk_from_metrics(volume_mm3: float, vdt_days: int) -> str:
    if volume_mm3 > 1500 or vdt_days < 100:
        return "high"
    if volume_mm3 > 500 or vdt_days < 200:
        return "medium"
    return "low"


def ensure_images() -> list[str]:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for idx in range(1, 6):
        path = IMAGE_DIR / f"ct_placeholder_{idx}.svg"
        path.write_bytes(SVG_BYTES)
        paths.append(f"mock_ct/{path.name}")
    return paths


def reset_data(db):
    for model in [
        AccessAudit,
        IngestionLog,
        QCTFollowup,
        QCTNodule,
        QCTSummary,
        Image,
        Series,
        Study,
        Patient,
        Site,
        Client,
        User,
    ]:
        db.query(model).delete()
    db.commit()


def main() -> None:
    random.seed(42)
    image_paths = ensure_images()
    db = SessionLocal()
    try:
        reset_data(db)

        user = User(username=settings.auth_fake_user, display_name="Demo Viewer", role="viewer")
        db.add(user)
        db.flush()

        client = Client(name="QCT Demo Client")
        db.add(client)
        db.flush()

        sites = [
            Site(client_id=client.id, name="Metro Imaging", location="Chicago"),
            Site(client_id=client.id, name="Harbor Diagnostics", location="Seattle"),
        ]
        db.add_all(sites)
        db.flush()

        patients = []
        for site in sites:
            for idx in range(1, 6):
                patient = Patient(
                    site_id=site.id,
                    patient_uid=f"P-{site.location[:2].upper()}-{idx:03d}",
                    anon_label=f"Anon-{site.location[:2].upper()}-{idx:03d}",
                    birth_year=random.randint(1950, 1995),
                    sex=random.choice(["F", "M"]),
                )
                patients.append(patient)
        db.add_all(patients)
        db.flush()

        studies = []
        for patient in patients:
            study_count = random.randint(2, 3)
            base_date = date.today() - timedelta(days=random.randint(40, 220))
            for s_idx in range(study_count):
                study_date = base_date + timedelta(days=s_idx * random.randint(60, 120))
                status = random.choice(STATUS_LEVELS)

                study = Study(
                    patient_id=patient.id,
                    site_id=patient.site_id,
                    study_uid=f"ST-{patient.patient_uid}-{s_idx + 1}",
                    study_date=study_date,
                    status=status,
                    overall_risk="low",
                    nodule_count=0,
                )
                db.add(study)
                db.flush()

                series = Series(
                    study_id=study.id,
                    series_uid=f"SR-{study.study_uid}",
                    description="Chest CT",
                )
                db.add(series)
                db.flush()

                image = Image(
                    series_id=series.id,
                    image_uid=str(uuid.uuid4()),
                    file_path=random.choice(image_paths),
                    thumbnail_path=None,
                )
                db.add(image)

                studies.append(study)

                LUNG_RADS_OPTS = ["2", "3", "4A", "4B"]
                TEXTURE_OPTS = ["Solid", "Part-Solid", "Ground Glass"]

                nodules = []
                nodule_count = random.randint(1, 4)
                for n_idx in range(nodule_count):
                    volume = random.uniform(50, 3000)
                    diameter = diameter_from_volume(volume) + random.uniform(-0.8, 0.8)
                    vdt_days = random.randint(30, 400)
                    risk = risk_from_metrics(volume, vdt_days)
                    nodules.append(
                        QCTNodule(
                            study=study,
                            nodule_uid=f"ND-{study.study_uid}-{n_idx + 1}",
                            location=random.choice(LOCATIONS),
                            volume_mm3=round(volume, 2),
                            diameter_mm=round(diameter, 2),
                            vdt_days=vdt_days,
                            risk=risk,
                            texture=random.choice(TEXTURE_OPTS),
                            is_followup=s_idx > 0,
                        )
                    )
                db.add_all(nodules)
                db.flush()

                volume_total = sum(n.volume_mm3 for n in nodules)
                mean_diameter = sum(n.diameter_mm for n in nodules) / len(nodules)
                mean_vdt = int(sum(n.vdt_days for n in nodules) / len(nodules))
                overall_risk = max([n.risk for n in nodules], key=RISK_LEVELS.index)
                
                # Lung-RADS logic (simplified)
                lrads = "2"
                if overall_risk == "high":
                    lrads = random.choice(["4A", "4B"])
                elif overall_risk == "medium":
                    lrads = "3"

                summary = QCTSummary(
                    study_id=study.id,
                    volume_total_mm3=round(volume_total, 2),
                    mean_diameter_mm=round(mean_diameter, 2),
                    vdt_days=mean_vdt,
                    overall_risk=overall_risk,
                    lung_rads=lrads,
                    algo_version=f"qCT v{random.randint(1,2)}.{random.randint(0,5)}",
                    notes="Simulated AI summary for demo use only.",
                )
                db.add(summary)

                study.overall_risk = overall_risk
                study.nodule_count = len(nodules)
                if overall_risk == "high":
                    study.status = "review"

                log = IngestionLog(
                    study_id=study.id,
                    status="completed" if study.status != "processing" else "processing",
                    message="Simulated ingestion event.",
                    started_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
                    completed_at=datetime.utcnow(),
                )
                db.add(log)

        db.flush()

        for patient in patients:
            patient_studies = [s for s in studies if s.patient_id == patient.id]
            patient_studies.sort(key=lambda s: s.study_date)
            for prev, curr in zip(patient_studies, patient_studies[1:]):
                prev_nodule = db.execute(
                    select(QCTNodule).where(QCTNodule.study_id == prev.id).limit(1)
                ).scalar_one_or_none()
                curr_nodule = db.execute(
                    select(QCTNodule).where(QCTNodule.study_id == curr.id).limit(1)
                ).scalar_one_or_none()
                if prev_nodule and curr_nodule:
                    followup = QCTFollowup(
                        nodule_id=curr_nodule.id,
                        prior_study_id=prev.id,
                        current_study_id=curr.id,
                        growth_percent=random.uniform(-5, 35),
                        status="stable" if curr.overall_risk == "low" else "monitor",
                    )
                    db.add(followup)

        for study in studies[:5]:
            db.add(
                AccessAudit(
                    user_id=user.id,
                    study_id=study.id,
                    action="seed_view",
                    ip_address="127.0.0.1",
                    accessed_at=datetime.utcnow(),
                )
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
