"""
Seeds the skills and tools master lists with the reference set from the
product spec. Idempotent — running it multiple times won't create
duplicates, since each insert checks for an existing row by name first.

Run with:  docker compose exec backend python -m app.seed.seed_data
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.ctf import CtfChallenge, CtfEvent
from app.models.finding import Finding
from app.models.lab import Lab, LabWriteup
from app.models.learning_goal import LearningGoal
from app.models.mitre import LabTechnique, MitreTechnique
from app.models.skill import Skill
from app.models.tool import Tool
from app.models.user import User

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


def _days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


# Ten sample labs matching the product spec's example list — enough
# realistic, varied content (categories, difficulties, statuses, dates,
# write-ups, skills/tools/techniques, structured findings) that the app
# doesn't look empty on first run, without being so much data it's hard
# to read through as a demo.
SAMPLE_LABS = [
    {
        "title": "Windows Event Log Investigation",
        "category": "SOC / Blue Team",
        "difficulty": "Medium",
        "status": "Completed",
        "platform": "TryHackMe",
        "date_started": _days_ago(40),
        "date_completed": _days_ago(39),
        "time_spent_minutes": 95,
        "objective": "Investigate a Windows host for signs of unauthorized access using Security event logs.",
        "environment": "Windows Server 2019, Event Viewer, Security log export.",
        "writeup": {
            "methodology": "Filtered the Security event log for Event ID 4624/4625 (logon success/failure) and sorted by account name and source IP.",
            "findings": "One local account had 40+ failed logon attempts within a 3-minute window, followed by a successful logon from the same source IP.",
            "analysis": "The pattern (many failures, then one success, same source) is classic brute-force-then-compromise. The account should be considered compromised.",
            "lessons_learned": "Event ID 4625 clustering by account+source is a fast, reliable brute-force indicator even without a SIEM.",
            "reflection": "Filtering raw Event Viewer XML by hand was slow — a real SIEM query would do this in seconds.",
            "next_steps": "Practice writing the equivalent detection as a Splunk search.",
        },
        "skills": ["Log Analysis", "Windows Security", "Incident Response"],
        "tools": ["PowerShell"],
        "technique": "T1110",
        "technique_justification": "The attack pattern (repeated failed logons followed by success) directly matches Brute Force.",
        "findings": [
            {"title": "Successful brute-force compromise", "severity": "High", "description": "Account 'svc_backup' compromised after 40+ failed attempts."},
        ],
    },
    {
        "title": "Brute Force Detection Lab",
        "category": "SOC / Blue Team",
        "difficulty": "Easy",
        "status": "Completed",
        "platform": "Home Lab",
        "date_started": _days_ago(35),
        "date_completed": _days_ago(35),
        "time_spent_minutes": 60,
        "objective": "Build a simple detection rule for SSH brute-force attempts on a Linux honeypot.",
        "environment": "Ubuntu 22.04 VM, auth.log, a scripted brute-force simulator.",
        "writeup": {
            "methodology": "Simulated brute-force attempts against SSH, then wrote a grep-based rule counting 'Failed password' lines per source IP per minute.",
            "findings": "Rule correctly flagged the simulated attacker IP after 5 failures within 60 seconds, with zero false positives from normal login traffic.",
            "analysis": "A simple frequency-based rule is enough to catch unsophisticated brute-force attempts; it would miss a slow, distributed attack.",
            "lessons_learned": "Detection thresholds always trade off false positives against missed slow attacks.",
            "reflection": None,
            "next_steps": "Test the same rule logic against a slow/distributed brute-force simulation.",
        },
        "skills": ["Threat Detection", "Linux"],
        "tools": ["Sysmon"],
        "technique": "T1110",
        "technique_justification": "Directly simulates and detects Brute Force against SSH.",
        "findings": [],
    },
    {
        "title": "Network Traffic Analysis",
        "category": "Network Security",
        "difficulty": "Medium",
        "status": "Completed",
        "platform": "TryHackMe",
        "date_started": _days_ago(30),
        "date_completed": _days_ago(29),
        "time_spent_minutes": 80,
        "objective": "Identify anomalous traffic patterns in a captured packet trace.",
        "environment": "Wireshark, a provided .pcap capture of a small office network.",
        "writeup": {
            "methodology": "Opened the capture in Wireshark, used protocol hierarchy statistics to find unusual protocol volume, then filtered by the suspicious host.",
            "findings": "One internal host made repeated DNS queries to newly-registered-looking domains, consistent with C2 beaconing.",
            "analysis": "Regular-interval DNS queries to unfamiliar domains from a single host is a classic beaconing signature.",
            "lessons_learned": "Protocol hierarchy stats are a fast first pass before diving into individual packets.",
            "reflection": None,
            "next_steps": "Learn to pivot from Wireshark into a DNS reputation lookup workflow.",
        },
        "skills": ["Network Analysis", "Threat Hunting"],
        "tools": ["Wireshark"],
        "technique": "T1071",
        "technique_justification": "The beaconing traffic uses DNS as its application-layer C2 channel.",
        "findings": [
            {"title": "Possible C2 beaconing", "severity": "Medium", "description": "Regular-interval DNS queries from one host to unfamiliar domains."},
        ],
    },
    {
        "title": "Web Application SQL Injection Lab",
        "category": "Web Security",
        "difficulty": "Medium",
        "status": "Completed",
        "platform": "HTB",
        "date_started": _days_ago(25),
        "date_completed": _days_ago(25),
        "time_spent_minutes": 70,
        "objective": "Identify and demonstrate a SQL injection vulnerability in a login form, in an authorized lab environment.",
        "environment": "Intentionally vulnerable web app provided by the platform, Burp Suite.",
        "writeup": {
            "methodology": "Used Burp Suite to intercept the login request, then tested classic injection payloads in the username field.",
            "findings": "A single-quote payload returned a database error, confirming the input was not parameterized.",
            "analysis": "The application concatenates user input directly into a SQL query, allowing authentication bypass.",
            "lessons_learned": "Parameterized queries / prepared statements are the correct fix, not input blacklisting.",
            "reflection": "Reproducing the exact bypass payload took a few tries.",
            "next_steps": "Practice the same class of bug against a different injection point (search field).",
        },
        "skills": ["Web Security"],
        "tools": ["Burp Suite"],
        "technique": None,
        "technique_justification": None,
        "findings": [
            {"title": "SQL injection in login form", "severity": "High", "description": "Unsanitized input allows authentication bypass."},
        ],
    },
    {
        "title": "Phishing Email Investigation",
        "category": "OSINT",
        "difficulty": "Easy",
        "status": "Completed",
        "platform": "TryHackMe",
        "date_started": _days_ago(20),
        "date_completed": _days_ago(20),
        "time_spent_minutes": 45,
        "objective": "Analyze a suspicious email for phishing indicators without executing any attachments.",
        "environment": "Sample .eml file, header analyzer, sandboxed VM for safe review.",
        "writeup": {
            "methodology": "Reviewed the email headers for sender/SPF/DKIM mismatches, then examined the attachment's filename and extension without opening it.",
            "findings": "The sender domain did not match the organization it claimed to represent, and SPF failed.",
            "analysis": "Header-level inconsistency between the claimed sender and the authenticated sending domain is a strong phishing indicator.",
            "lessons_learned": "SPF/DKIM failures are often visible before ever touching the message body or attachment.",
            "reflection": None,
            "next_steps": "Practice extracting IOCs (sender domain, URLs) into a simple report format.",
        },
        "skills": ["OSINT"],
        "tools": [],
        "technique": "T1566",
        "technique_justification": "The email itself is a phishing attempt using a spoofed sender domain.",
        "findings": [],
    },
    {
        "title": "Linux Privilege Escalation Lab",
        "category": "Linux",
        "difficulty": "Hard",
        "status": "In Progress",
        "platform": "HTB",
        "date_started": _days_ago(8),
        "date_completed": None,
        "time_spent_minutes": 50,
        "objective": "Escalate from a low-privileged shell to root on an intentionally vulnerable Linux box.",
        "environment": "Ubuntu-based vulnerable VM, authorized lab environment.",
        "writeup": {
            "methodology": "Ran standard enumeration (sudo -l, SUID binaries, cron jobs) to look for a privilege escalation path.",
            "findings": "Still enumerating — found one world-writable cron script but haven't confirmed exploitability yet.",
            "analysis": None,
            "lessons_learned": None,
            "reflection": None,
            "next_steps": "Confirm whether the cron script actually runs as root, then attempt the escalation.",
        },
        "skills": ["Linux", "Vulnerability Management"],
        "tools": ["Kali Linux"],
        "technique": None,
        "technique_justification": None,
        "findings": [],
    },
    {
        "title": "PCAP Investigation",
        "category": "Network Security",
        "difficulty": "Medium",
        "status": "Completed",
        "platform": "Home Lab",
        "date_started": _days_ago(15),
        "date_completed": _days_ago(14),
        "time_spent_minutes": 65,
        "objective": "Reconstruct a file transferred over an unencrypted protocol from a packet capture.",
        "environment": "Wireshark, a provided FTP capture.",
        "writeup": {
            "methodology": "Used Wireshark's 'Follow TCP Stream' and File > Export Objects to pull the transferred file out of the capture.",
            "findings": "The exported file was a configuration file containing a plaintext password.",
            "analysis": "Transferring credentials over unencrypted FTP exposes them to anyone who can capture the traffic.",
            "lessons_learned": "Export Objects is much faster than manually reconstructing a transfer byte-by-byte.",
            "reflection": None,
            "next_steps": "Repeat the exercise against an encrypted (FTPS/SFTP) capture to confirm it can't be done the same way.",
        },
        "skills": ["Network Analysis", "Digital Forensics"],
        "tools": ["Wireshark"],
        "technique": None,
        "technique_justification": None,
        "findings": [
            {"title": "Plaintext credentials in transferred file", "severity": "Medium", "description": "Config file with a plaintext password recovered from unencrypted FTP traffic."},
        ],
    },
    {
        "title": "PowerShell Threat Detection",
        "category": "Windows Security",
        "difficulty": "Medium",
        "status": "Completed",
        "platform": "TryHackMe",
        "date_started": _days_ago(10),
        "date_completed": _days_ago(9),
        "time_spent_minutes": 75,
        "objective": "Detect obfuscated/encoded PowerShell execution from Windows event logs.",
        "environment": "Windows 10 VM with PowerShell script block logging enabled, Sysmon.",
        "writeup": {
            "methodology": "Searched Sysmon Event ID 1 (process creation) for powershell.exe with a '-enc' or '-EncodedCommand' argument.",
            "findings": "Found a process creation event with a base64-encoded command line launched from a Word document's parent process.",
            "analysis": "Office spawning encoded PowerShell is a strong indicator of a malicious macro.",
            "lessons_learned": "Parent-child process relationships (Office -> PowerShell) are often more telling than the command alone.",
            "reflection": None,
            "next_steps": "Practice decoding the base64 payload safely in an isolated sandbox.",
        },
        "skills": ["Threat Detection", "Windows Security"],
        "tools": ["Sysmon", "PowerShell"],
        "technique": "T1059.001",
        "technique_justification": "Encoded command execution via PowerShell directly matches this technique.",
        "findings": [
            {"title": "Encoded PowerShell spawned from Office", "severity": "High", "description": "powershell.exe -enc launched as a child of winword.exe."},
        ],
    },
    {
        "title": "Vulnerability Assessment Lab",
        "category": "Vulnerability Management",
        "difficulty": "Easy",
        "status": "Completed",
        "platform": "Home Lab",
        "date_started": _days_ago(5),
        "date_completed": _days_ago(5),
        "time_spent_minutes": 40,
        "objective": "Run and interpret a vulnerability scan against a deliberately outdated lab VM.",
        "environment": "Local VM with intentionally outdated packages, Nmap with NSE vuln scripts.",
        "writeup": {
            "methodology": "Ran an Nmap scan with version detection and vulnerability scripts against the target.",
            "findings": "Identified an outdated service version with a publicly known CVE.",
            "analysis": "Version-based scanning is fast but only as good as its vulnerability database — it can't find logic flaws.",
            "lessons_learned": "Always confirm a flagged CVE actually applies to the specific configuration, not just the version string.",
            "reflection": None,
            "next_steps": "Practice validating a scanner finding manually instead of trusting it outright.",
        },
        "skills": ["Vulnerability Management"],
        "tools": ["Nmap"],
        "technique": None,
        "technique_justification": None,
        "findings": [
            {"title": "Outdated service with known CVE", "severity": "Medium", "description": "Flagged by Nmap NSE vuln scripts; confirmed version match."},
        ],
    },
    {
        "title": "Incident Response Simulation",
        "category": "Incident Response",
        "difficulty": "Hard",
        "status": "Planned",
        "platform": "TryHackMe",
        "date_started": None,
        "date_completed": None,
        "time_spent_minutes": None,
        "objective": "Walk through a full incident response lifecycle (detection, containment, eradication, recovery) for a simulated ransomware incident.",
        "environment": "Not started yet.",
        "writeup": {
            "methodology": None, "findings": None, "analysis": None,
            "lessons_learned": None, "reflection": None, "next_steps": None,
        },
        "skills": [],
        "tools": [],
        "technique": None,
        "technique_justification": None,
        "findings": [],
    },
]

SAMPLE_CTF_EVENT = {"name": "PicoCTF 2026", "platform": "PicoCTF", "event_date": _days_ago(18)}

SAMPLE_CTF_CHALLENGES = [
    {
        "title": "Basic RSA",
        "category": "Crypto",
        "difficulty": "Easy",
        "status": "Solved",
        "time_spent_minutes": 30,
        "description": "Recover a message encrypted with weak RSA parameters.",
        "solution_writeup": "The modulus was small enough to factor directly, which gave the private key and let me decrypt the ciphertext.",
        "lessons_learned": "Small RSA moduli are trivially factorable — key size matters as much as the algorithm choice.",
    },
    {
        "title": "Cookie Monster",
        "category": "Web",
        "difficulty": "Easy",
        "status": "Solved",
        "time_spent_minutes": 25,
        "description": "Bypass authentication by inspecting and modifying a session cookie.",
        "solution_writeup": "The cookie was a base64-encoded JSON object with no signature. Decoding it, changing 'role' to 'admin', and re-encoding it granted admin access.",
        "lessons_learned": "Session state must be signed or encrypted server-side — client-readable state is client-modifiable state.",
    },
    {
        "title": "Memory Lane",
        "category": "Forensics",
        "difficulty": "Medium",
        "status": "Partially Solved",
        "time_spent_minutes": 50,
        "description": "Extract a hidden flag from a memory dump.",
        "solution_writeup": "Identified the suspicious process in the memory image but haven't finished extracting the embedded string yet.",
        "lessons_learned": "Memory analysis tooling has a steep learning curve compared to disk forensics.",
    },
    {
        "title": "Shellcode 101",
        "category": "Pwn",
        "difficulty": "Hard",
        "status": "Unsolved",
        "time_spent_minutes": 40,
        "description": "Exploit a basic buffer overflow to achieve code execution.",
        "solution_writeup": None,
        "lessons_learned": "Still building the foundational assembly/stack knowledge this challenge assumes.",
    },
    {
        "title": "Find The Person",
        "category": "OSINT",
        "difficulty": "Easy",
        "status": "Solved",
        "time_spent_minutes": 20,
        "description": "Identify a fictional person from publicly available (challenge-provided) social media posts.",
        "solution_writeup": "Cross-referenced usernames and a background detail visible in one photo to find the matching profile the challenge was looking for.",
        "lessons_learned": "Small, easily-overlooked details in images are often the fastest OSINT lead.",
    },
]

# The exact roadmap tree from the product spec. Items linked to an
# existing skill name get real computed progress; the rest are pure
# grouping nodes, which is a deliberate mix so sample data demonstrates
# both kinds of goal.
SAMPLE_ROADMAP = {
    "title": "SOC Analyst",
    "children": [
        {"title": "Networking", "skill": None},
        {"title": "Linux", "skill": "Linux"},
        {"title": "Windows Event Logs", "skill": None},
        {"title": "SIEM", "skill": "SIEM"},
        {"title": "Detection Engineering", "skill": None},
        {"title": "Threat Hunting", "skill": "Threat Hunting"},
        {"title": "Incident Response", "skill": "Incident Response"},
    ],
}


def seed_sample_labs(db: Session, user_id) -> int:
    created = 0
    for entry in SAMPLE_LABS:
        if db.query(Lab).filter(Lab.user_id == user_id, Lab.title == entry["title"]).first():
            continue

        lab = Lab(
            user_id=user_id,
            title=entry["title"],
            platform=entry["platform"],
            category=entry["category"],
            difficulty=entry["difficulty"],
            status=entry["status"],
            date_started=entry["date_started"],
            date_completed=entry["date_completed"],
            time_spent_minutes=entry["time_spent_minutes"],
            objective=entry["objective"],
            environment=entry["environment"],
        )
        db.add(lab)
        db.flush()

        db.add(LabWriteup(lab_id=lab.id, **entry["writeup"]))

        for skill_name in entry["skills"]:
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if skill:
                lab.skills.append(skill)

        for tool_name in entry["tools"]:
            tool = db.query(Tool).filter(Tool.name == tool_name).first()
            if tool:
                lab.tools.append(tool)

        if entry["technique"]:
            technique = db.query(MitreTechnique).filter(MitreTechnique.technique_id == entry["technique"]).first()
            if technique:
                db.add(LabTechnique(lab_id=lab.id, technique_id=technique.id, justification=entry["technique_justification"]))

        for finding in entry["findings"]:
            db.add(Finding(lab_id=lab.id, title=finding["title"], description=finding["description"], severity=finding["severity"]))

        created += 1

    db.commit()
    return created


def seed_sample_ctf(db: Session, user_id) -> int:
    if db.query(CtfEvent).filter(CtfEvent.user_id == user_id, CtfEvent.name == SAMPLE_CTF_EVENT["name"]).first():
        return 0

    event = CtfEvent(user_id=user_id, **SAMPLE_CTF_EVENT)
    db.add(event)
    db.flush()

    for challenge in SAMPLE_CTF_CHALLENGES:
        db.add(CtfChallenge(ctf_event_id=event.id, **challenge))

    db.commit()
    return len(SAMPLE_CTF_CHALLENGES)


def seed_sample_roadmap(db: Session, user_id) -> int:
    if db.query(LearningGoal).filter(LearningGoal.user_id == user_id, LearningGoal.title == SAMPLE_ROADMAP["title"]).first():
        return 0

    root = LearningGoal(user_id=user_id, title=SAMPLE_ROADMAP["title"])
    db.add(root)
    db.flush()

    created = 1
    for child in SAMPLE_ROADMAP["children"]:
        skill_id = None
        if child["skill"]:
            skill = db.query(Skill).filter(Skill.name == child["skill"]).first()
            skill_id = skill.id if skill else None
        db.add(LearningGoal(user_id=user_id, title=child["title"], parent_goal_id=root.id, related_skill_id=skill_id))
        created += 1

    db.commit()
    return created


def seed_sample_data_for_user(db: Session, user_id) -> None:
    """Seeds sample labs, a CTF event with challenges, and the roadmap tree for one user. Call seed_skills_and_tools() first."""
    labs_created = seed_sample_labs(db, user_id)
    ctf_created = seed_sample_ctf(db, user_id)
    goals_created = seed_sample_roadmap(db, user_id)
    print(f"Seeded {labs_created} sample lab(s), {ctf_created} sample CTF challenge(s), {goals_created} roadmap goal(s).")


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

        user = session.query(User).first()
        if user is None:
            print(
                "\nNo user account exists yet, so sample labs/CTFs/roadmap were skipped. "
                "Register your account first (via the app, at /register), then re-run this script "
                "to add sample data for that account."
            )
        else:
            seed_sample_data_for_user(session, user.id)
    finally:
        session.close()
