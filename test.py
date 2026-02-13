import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import Client
from bs4 import BeautifulSoup

from Exactus.payroll.models import PayrollPeriod

PERIOD_ID = int(os.environ.get("PERIOD_ID", "6"))
OUT = Path(f"/tmp/period_detail_ui_check_{PERIOD_ID}.html")

period = PayrollPeriod.objects.select_related(
    "payroll__country", "payroll__company"
).get(pk=PERIOD_ID)

url = f"/{period.payroll.country.slug}/{period.payroll.company.company_id}/payroll/{period.payroll.id}/period/{period.id}/"

User = get_user_model()
user = User.objects.filter(is_superuser=True).first() or User.objects.first()
assert user, "No users found"

c = Client()
c.force_login(user)

print("=" * 80)
print("UI CHECK (authenticated HTTP)")
print("=" * 80)
print("URL:", url)
print("User:", user)
print("Period:", period)

# Force host so it doesn't crash on ALLOWED_HOSTS
resp = c.get(url, SERVER_NAME="127.0.0.1", SERVER_PORT="8000", HTTP_HOST="127.0.0.1")
print("HTTP status:", resp.status_code)

html = resp.content.decode("utf-8", errors="ignore")
OUT.write_text(html, encoding="utf-8")
print("Saved:", str(OUT), "len:", len(html))

# Basic string checks
for s in ["Gross Pay", "Net Salary", "Income Tax", "National Insurance"]:
    print(f"Contains '{s}'?:", s in html)

soup = BeautifulSoup(html, "html.parser")

ths = soup.find_all("th")
print("\nTH total:", len(ths))

th_texts = []
hidden_ths = []

for th in ths:
    text = " ".join(th.get_text(" ", strip=True).split())
    if not text:
        continue
    th_texts.append(text)

    style = (th.get("style") or "").lower()
    cls = " ".join(th.get("class") or []).lower()

    if "display:none" in style or "d-none" in cls or "hidden" in cls:
        hidden_ths.append(text)

print("\nFirst 30 TH labels:")
for t in th_texts[:30]:
    print(" -", t)

print("\nHidden TH labels (inline/class):")
for t in hidden_ths[:50]:
    print(" -", t)

print("\nDONE.")
