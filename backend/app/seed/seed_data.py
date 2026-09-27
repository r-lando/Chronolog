"""
Seeds the skills and tools master lists with the reference set from the
product spec. Idempotent — running it multiple times won't create
duplicates, since each insert checks for an existing row by name first.

Run with:  docker compose exec backend python -m app.seed.seed_data
"""

from app.database import SessionLocal
from app.models.skill import Skill
from app.models.tool import Tool

SKILLS = [
    ("Log Analysis", "SOC / Blue Team"),
    ("SIEM", "SOC / Blue Team"),
    ("Threat Detection", "SOC / Blue Team"),
    ("Incident Response", "SOC / Blue Team"),
    ("Network Analysis", "Network Security"),
    ("Web Security", "Web Security"),
    ("Digital Forensics", "Digital Forensics"),
    ("Malware Analysis", "Malware Analysis"),
    ("Linux", "Systems"),
    ("Windows Security", "Systems"),
    ("Vulnerability Management", "Vulnerability Management"),
    ("Threat Hunting", "Threat Hunting"),
    ("GRC", "GRC"),
    ("OSINT", "OSINT"),
    ("Cryptography", "Cryptography"),
    ("Cloud Security", "Cloud Security"),
]

TOOLS = [
    ("Wireshark", "Network Analysis"),
    ("Nmap", "Network Security"),
    ("Burp Suite", "Web Security"),
    ("Splunk", "SIEM"),
    ("Elastic", "SIEM"),
    ("Volatility", "Digital Forensics"),
    ("Autopsy", "Digital Forensics"),
    ("Kali Linux", "Platform"),
    ("PowerShell", "Systems"),
    ("Sysmon", "Threat Detection"),
]


def seed_skills_and_tools() -> None:
    db = SessionLocal()
    try:
        created_skills = 0
        for name, category in SKILLS:
            if not db.query(Skill).filter(Skill.name == name).first():
                db.add(Skill(name=name, category=category))
                created_skills += 1

        created_tools = 0
        for name, category in TOOLS:
            if not db.query(Tool).filter(Tool.name == name).first():
                db.add(Tool(name=name, category=category))
                created_tools += 1

        db.commit()
        print(f"Seeded {created_skills} new skill(s) and {created_tools} new tool(s).")
    finally:
        db.close()


if __name__ == "__main__":
    seed_skills_and_tools()
