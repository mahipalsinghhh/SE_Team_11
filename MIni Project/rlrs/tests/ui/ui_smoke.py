"""Browser smoke test (not collected by pytest). Needs: pip install playwright && playwright install chromium.
Usage: python tests/ui/ui_smoke.py   -> prints PASS/FAIL per step and saves screenshots to tests/ui/screenshots/"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
SHOTS = Path(__file__).parent / "screenshots"
SHOTS.mkdir(exist_ok=True)
PORT = 8765
results = []


def step(name, fn):
    try:
        fn()
        results.append((name, True, ""))
        print("PASS", name)
    except Exception as e:  # noqa
        results.append((name, False, str(e).splitlines()[0][:200]))
        print("FAIL", name, "-", str(e).splitlines()[0][:200])


def main():
    tmp = tempfile.mkdtemp()
    proc = subprocess.Popen([sys.executable, "-m", "rlrs_app.server", "--db", f"{tmp}/ui.db", "--port", str(PORT), "--seed", "--quiet"],
                            cwd=tmp, env={**os.environ, "PYTHONPATH": str(ROOT)}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/"); break
            except Exception:
                time.sleep(0.2)
        base = f"http://127.0.0.1:{PORT}"
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("dialog", lambda d: d.accept("Printer reserved for class" if d.type == "prompt" else None))

            def login(email, pw):
                page.goto(base)
                page.fill("#email", email); page.fill("#pw", pw)
                page.click("button[type=submit]")
                expect(page.locator("#logout")).to_be_visible()

            def bad_login():
                page.goto(base); page.fill("#email", "student1@lab.test"); page.fill("#pw", "wrong")
                page.click("button[type=submit]")
                expect(page.locator("#msg")).to_contain_text("Invalid email or password")
            step("login with wrong password shows error", bad_login)

            def book():
                login("student1@lab.test", "student123")
                expect(page.locator("table.grid")).to_be_visible()
                page.screenshot(path=str(SHOTS / "01_calendar.png"))
                free = page.locator("button.slot.free")
                assert free.count() > 0, "no free slots"
                free.last.click()
                expect(page.locator("#bookbtn")).to_be_visible()
                page.click("#bookbtn")
                expect(page.locator("#msg")).to_contain_text("Reservation confirmed")
                expect(page.locator("button.slot.own").first).to_be_visible()
                page.screenshot(path=str(SHOTS / "02_booked.png"))
            step("student books a free slot; it shows as Yours", book)

            def conflict_via_api():
                req = urllib.request.Request(base + "/api/login", method="POST", data=json.dumps({"email": "student2@lab.test", "password": "student123"}).encode(), headers={"Content-Type": "application/json"})
                cookie = urllib.request.urlopen(req).headers["Set-Cookie"].split(";")[0]
                mine = json.loads(urllib.request.urlopen(urllib.request.Request(base + "/api/reservations/mine", headers={"Cookie": cookie})).read())
                assert mine == []
            step("other student sees no reservations of student1", conflict_via_api)

            def mine_and_cancel():
                page.click("button[role=tab]:has-text('My reservations')")
                expect(page.locator("table tbody tr")).to_have_count(1)
                expect(page.locator(".tag.Confirmed")).to_be_visible()
                page.screenshot(path=str(SHOTS / "03_my_reservations.png"))
                page.click("button.danger:has-text('Cancel')")
                expect(page.locator(".tag.Cancelled")).to_be_visible()
            step("My reservations lists it; cancel works", mine_and_cancel)

            def rebook_then_maintenance():
                page.click("button[role=tab]:has-text('Calendar')")
                page.locator("button.slot.free").last.click(); page.click("#bookbtn")
                expect(page.locator("#msg")).to_contain_text("Reservation confirmed")
                page.click("#logout")
                login("incharge@lab.test", "incharge123")
                page.click("button[role=tab]:has-text('Manage')")
                expect(page.locator("text=Pending approvals")).to_be_visible()
                page.screenshot(path=str(SHOTS / "04_manage.png"))
                # block the whole upcoming fortnight for equipment 1 -> cancels the booking
                page.select_option("#meq", index=0)
                page.fill("#ms", "2026-01-01T00:00"); page.fill("#mt", "2099-01-01T00:00"); page.fill("#mr", "calibration")
                page.click("button:has-text('Create block')")
                expect(page.locator("#msg")).to_contain_text("1 reservation(s) cancelled")
            step("staff maintenance block cancels the student's booking", rebook_then_maintenance)

            def student_sees_maintenance():
                page.click("#logout")
                login("student1@lab.test", "student123")
                expect(page.locator("button.slot.maintenance").first).to_be_visible()
                assert page.locator("button.slot.free").count() == 0
                page.screenshot(path=str(SHOTS / "05_maintenance.png"))
            step("student sees maintenance slots, none free", student_sees_maintenance)

            def staff_report():
                page.click("#logout")
                login("incharge@lab.test", "incharge123")
                page.click("button[role=tab]:has-text('Reports')")
                page.click("button:has-text('Run report')")
                expect(page.locator("#report")).to_contain_text("Digital Oscilloscope")
                page.screenshot(path=str(SHOTS / "06_report.png"))
            step("staff report renders", staff_report)

            def student_has_no_staff_tabs():
                page.click("#logout"); login("student1@lab.test", "student123")
                assert page.locator("button[role=tab]:has-text('Manage')").count() == 0
            step("students have no Manage/Reports tabs", student_has_no_staff_tabs)

            step("no JavaScript errors in the page", lambda: (_ for _ in ()).throw(AssertionError(errors[0])) if errors else None)
            b.close()
    finally:
        proc.terminate()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} UI steps passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
