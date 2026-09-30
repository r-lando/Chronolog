"""
Seeds the skills and tools master lists with the reference set from the
product spec. Idempotent — running it multiple times won't create
duplicates, since each insert checks for an existing row by name first.

Run with:  docker compose exec backend python -m app.seed.seed_data
"""

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.mitre import MitreTechnique
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

# A curated, representative subset of MITRE ATT&CK (Enterprise matrix) —
# not the full framework, which has 600+ techniques and would be far
# beyond what a personal lab journal needs. Each entry uses the real,
# official MITRE technique ID and name; descriptions are written in
# plain language for a student audience rather than quoted from MITRE's
# site. Where a technique maps to multiple tactics in the real ATT&CK
# matrix, one representative primary tactic is used here for simplicity.
MITRE_TECHNIQUES = [
    ("T1110", None, "Brute Force", "Credential Access",
     "Repeatedly guessing passwords or keys to gain unauthorized access to an account."),
    ("T1059", None, "Command and Scripting Interpreter", "Execution",
     "Using a command-line shell or scripting language to execute commands or scripts."),
    ("T1059.001", "T1059", "PowerShell", "Execution",
     "Using Windows PowerShell specifically to execute commands, scripts, or payloads."),
    ("T1078", None, "Valid Accounts", "Defense Evasion",
     "Using legitimate, compromised credentials to access systems while blending in with normal activity."),
    ("T1566", None, "Phishing", "Initial Access",
     "Sending fraudulent messages to trick a user into revealing information or running malicious content."),
    ("T1566.001", "T1566", "Spearphishing Attachment", "Initial Access",
     "A targeted phishing email carrying a malicious file attachment."),
    ("T1046", None, "Network Service Discovery", "Discovery",
     "Enumerating services running on remote systems, often via port scanning."),
    ("T1018", None, "Remote System Discovery", "Discovery",
     "Identifying other systems on a network by IP, hostname, or other means."),
    ("T1021", None, "Remote Services", "Lateral Movement",
     "Using legitimate remote access services (RDP, SSH, etc.) to move between systems."),
    ("T1021.001", "T1021", "Remote Desktop Protocol", "Lateral Movement",
     "Using RDP specifically to log into and control a remote system."),
    ("T1053", None, "Scheduled Task/Job", "Persistence",
     "Abusing task scheduling utilities to run malicious code at a specific time or on a recurring basis."),
    ("T1055", None, "Process Injection", "Defense Evasion",
     "Injecting code into the address space of another process to evade detection or gain its privileges."),
    ("T1082", None, "System Information Discovery", "Discovery",
     "Gathering details about a system's configuration, such as OS version and hardware."),
    ("T1003", None, "OS Credential Dumping", "Credential Access",
     "Extracting stored credentials from an operating system's memory or credential stores."),
    ("T1071", None, "Application Layer Protocol", "Command and Control",
     "Blending malicious command-and-control traffic into common protocols like HTTP or DNS."),
    ("T1105", None, "Ingress Tool Transfer", "Command and Control",
     "Transferring tools or files onto a compromised system from an external source."),
    ("T1486", None, "Data Encrypted for Impact", "Impact",
     "Encrypting data on target systems to disrupt availability, as in ransomware."),
    ("T1027", None, "Obfuscated Files or Information", "Defense Evasion",
     "Encoding, encrypting, or otherwise disguising malicious content to evade detection."),
]


def seed_skills_and_tools(db: Session) -> None:
    """
    Seeds the given session with skills, tools, and MITRE techniques.

    Takes a Session rather than creating its own: app.database.SessionLocal
    is bound to whatever DATABASE_URL is configured for this process,
    which in the test suite is not the same database the tests actually
    run against (an isolated in-memory SQLite session per test). Accepting
    the session as a parameter lets both the CLI entry point below and
    the test suite share this exact seeding logic safely.
    """
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

    created_techniques = 0
    for technique_id, sub_technique_id, name, tactic, description in MITRE_TECHNIQUES:
        if not db.query(MitreTechnique).filter(MitreTechnique.technique_id == technique_id).first():
            db.add(
                MitreTechnique(
                    technique_id=technique_id,
                    sub_technique_id=sub_technique_id,
                    name=name,
                    tactic=tactic,
                    description=description,
                )
            )
            created_techniques += 1

    db.commit()
    print(
        f"Seeded {created_skills} new skill(s), {created_tools} new tool(s), "
        f"and {created_techniques} new MITRE technique(s)."
    )


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed_skills_and_tools(session)
    finally:
        session.close()
