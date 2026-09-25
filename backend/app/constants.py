"""
Controlled vocabularies for lab classification.

These are enforced as plain Python lists validated in Pydantic (not as
a Postgres ENUM type) so that adding a category later is a one-line
code change and a data migration, not a schema migration that locks
the column type. The trade-off is explicit validation in the schema
layer instead of database-level enforcement — acceptable for a
single-user learning journal where the data never comes from an
untrusted external system.
"""

LAB_CATEGORIES = [
    "SOC / Blue Team",
    "Network Security",
    "Web Security",
    "Digital Forensics",
    "Incident Response",
    "Malware Analysis",
    "OSINT",
    "Cryptography",
    "Cloud Security",
    "GRC",
    "Linux",
    "Windows Security",
    "Threat Hunting",
    "Vulnerability Management",
    "CTF",
]

LAB_DIFFICULTIES = ["Beginner", "Easy", "Medium", "Hard", "Expert"]

LAB_STATUSES = ["Planned", "In Progress", "Completed", "Paused", "Archived"]
