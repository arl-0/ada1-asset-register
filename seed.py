"""
seed.py — Creates the database tables and inserts demo data on first run.

Called automatically by start.sh on every Render deployment.
Safe to re-run: checks whether data already exists before inserting.
"""

import os
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, ADAEntry


def seed():
    app = create_app()

    with app.app_context():
        # Create all tables (no-op if they already exist)
        db.create_all()

        # Only seed if the database is empty
        if User.query.count() > 0:
            print("Database already seeded — skipping.")
            return

        print("Seeding database...")

        # ── Users ──────────────────────────────────────────────────────────
        admin = User(
            username="admin",
            password=generate_password_hash("Admin1234!"),
            clearance=5,
            role="admin",
        )
        researcher = User(
            username="bob.researcher",
            password=generate_password_hash("Research99"),
            clearance=2,
            role="regular",
        )
        db.session.add_all([admin, researcher])
        db.session.flush()   # populate IDs before referencing them

        # ── Sample asset entries ───────────────────────────────────────────
        entries = [
            ADAEntry(
                asset_number="ADA-001",
                title="Server Rack 3B — Procurement Record",
                content=(
                    "Dell PowerEdge R740. Serial: DPE-3B-0042. "
                    "Warranty contract ref CW-2291. Serviced March 2026. "
                    "Location: Server Room B, Site 9."
                ),
                redacted_text="[REDACTED] IT asset procurement record. Clearance Level 1 required.",
                clearance_level=1,
                created_by=admin.id,
            ),
            ADAEntry(
                asset_number="ADA-002",
                title="Software Licence — Site-Wide (MS365)",
                content=(
                    "Microsoft 365 E3 site-wide licence. "
                    "Agreement ref MS-E3-ORG-0091. Renewal due January 2027. "
                    "Contact: procurement@internal."
                ),
                redacted_text="[REDACTED] Licence contract record. Clearance Level 1 required.",
                clearance_level=1,
                created_by=admin.id,
            ),
            ADAEntry(
                asset_number="ADA-003",
                title="Operations Log — Site 9 Inspection",
                content=(
                    "Routine site inspection completed 14/06/2026. "
                    "No anomalies reported. Fire suppression system tested — operational. "
                    "Access logs reviewed — no unauthorised entries."
                ),
                redacted_text="[REDACTED] Operations log entry. Clearance Level 2 required.",
                clearance_level=2,
                created_by=admin.id,
            ),
            ADAEntry(
                asset_number="ADA-004",
                title="Operations Log — Network Audit Q2 2026",
                content=(
                    "Quarterly network audit completed. "
                    "3 deprecated VLANs removed. Firewall rules reviewed and updated. "
                    "No critical findings. Full report filed under NET-AUDIT-Q2-2026."
                ),
                redacted_text="[REDACTED] Network operations record. Clearance Level 2 required.",
                clearance_level=2,
                created_by=admin.id,
            ),
            ADAEntry(
                asset_number="ADA-005",
                title="Research Task RT-118 — Interim Summary",
                content=(
                    "Interim summary for Research Task RT-118. "
                    "Phase 1 containment trials completed. Preliminary results within expected parameters. "
                    "Full technical briefing restricted to Level 4+ personnel. "
                    "Next review scheduled Q3 2026."
                ),
                redacted_text="[REDACTED] Research task summary. Clearance Level 4 required.",
                clearance_level=4,
                created_by=admin.id,
            ),
            ADAEntry(
                asset_number="ADA-006",
                title="Research Task RT-119 — Classified Briefing",
                content=(
                    "Full classified briefing for RT-119. "
                    "Details restricted to Level 5 personnel only. "
                    "Contact Lead Researcher for access request procedure."
                ),
                redacted_text="[REDACTED] Classified research record. Clearance Level 5 required.",
                clearance_level=5,
                created_by=admin.id,
            ),
        ]

        db.session.add_all(entries)
        db.session.commit()
        print(f"Seeded {len(entries)} entries and 2 users.")


if __name__ == "__main__":
    seed()
