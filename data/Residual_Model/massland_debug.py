from playwright.sync_api import sync_playwright
import re, time, csv, random
from datetime import datetime


OUT = "deed_export.csv"
SLOW_MO_MS = 80

POST_CLICK_EXTRA_WAIT_RANGE = (0.8, 1.4)
ROW_SLEEP_RANGE = (0.6, 1.2)
PAGE_SLEEP_RANGE = (1.8, 3.0)

DETAIL_TIMEOUT_MS = 20000
NEXT_TIMEOUT_MS = 15000

book_link_re = re.compile(r"^\d+/\d+$")

def now_tag():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def jitter_sleep(a_b):
    """a_b: (min, max) seconds"""
    time.sleep(random.uniform(a_b[0], a_b[1]))

def get_left_table(page):
    left_table = page.locator(
        "table",
        has=page.get_by_role("cell", name="File Date Book/Page Type Desc")
    ).filter(has_text="Add to Basket")

    cnt = left_table.count()
    if cnt != 1:
        raise RuntimeError(f"left_table count = {cnt} (expectation=1).")
    return left_table


X_DETAIL_TABLE = "xpath=(//table[.//*[normalize-space()='Doc. #'] and .//*[normalize-space()='Book/Page'] and .//*[normalize-space()='Consideration']])[1]"
X_FILE_DATE_VAL = f"{X_DETAIL_TABLE}//tr[2]/td[2]"   
X_BOOKPAGE_VAL = f"{X_DETAIL_TABLE}//tr[2]/td[6]"
X_CONSIDERATION_VAL = f"{X_DETAIL_TABLE}//tr[2]/td[7]"

X_STREET_TABLE = (
    "xpath=(//table["
    ".//*[self::th or self::td][normalize-space()='Street #'] and "
    ".//*[self::th or self::td][normalize-space()='Street Name'] and "
    ".//*[self::th or self::td][normalize-space()='Description'] and "
    "not(.//*[normalize-space()='Doc. #'])"
    "])[1]"
)
X_STREET_NO_VAL = f"{X_STREET_TABLE}//tr[2]/td[1]"
X_STREET_NAME_VAL = f"{X_STREET_TABLE}//tr[2]/td[2]"

def safe_text(page, xp: str, timeout_ms: int = 8000) -> str:
    return page.locator(xp).first.inner_text(timeout=timeout_ms).strip()

def wait_bookpage_equals(page, expected_bp: str, timeout_ms: int = DETAIL_TIMEOUT_MS):
    loc = page.locator(X_BOOKPAGE_VAL).first
    deadline = time.time() + (timeout_ms / 1000.0)

    try:
        loc.wait_for(timeout=min(timeout_ms, 5000))
    except:
        pass

    last = ""
    while time.time() < deadline:
        try:
            txt = loc.inner_text(timeout=1200).strip()
            last = txt
            if txt == expected_bp:
                return
        except:
            pass
        time.sleep(0.12)

    raise TimeoutError(f"Book/Page not updated to {expected_bp}. last={last!r}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=SLOW_MO_MS)
        page = browser.new_page()
        page.goto("https://www.masslandrecords.com/suffolk/D/Default.aspx")

        input("Please set all conditions, click Search, then come back to terminal to press Enter to start")

        seen = set()    
        rows_out = []       
        page_no = 1

        while True:
            left_table = get_left_table(page)
            book_links = left_table.get_by_role("link").filter(has_text=book_link_re)
            n = book_links.count()

            if n == 0:
                print("book/page links = 0, stop。")
                break

            print(f"[Page {page_no}] book/page links={n}")
            first_bp_before = book_links.nth(0).inner_text().strip()

            for i in range(n):
                left_table = get_left_table(page)
                book_links = left_table.get_by_role("link").filter(has_text=book_link_re)

                link = book_links.nth(i)
                bp_left = link.inner_text().strip()

                link.click()

                try:
                    wait_bookpage_equals(page, bp_left, timeout_ms=DETAIL_TIMEOUT_MS)
                    jitter_sleep(POST_CLICK_EXTRA_WAIT_RANGE)

                    bp = safe_text(page, X_BOOKPAGE_VAL)
                    file_date = safe_text(page, X_FILE_DATE_VAL)
                    consideration = safe_text(page, X_CONSIDERATION_VAL)
                    street_number = safe_text(page, X_STREET_NO_VAL)
                    street_name = safe_text(page, X_STREET_NAME_VAL)

                    if bp in seen:
                        jitter_sleep(ROW_SLEEP_RANGE)
                        continue
                    seen.add(bp)

                    rows_out.append([bp, file_date, street_number, street_name, consideration])
                    print(f"  {bp} | {file_date} | {street_number} | {street_name} | {consideration}")

                except Exception as e:
                    shot = f"debug_p{page_no}_i{i}_{now_tag()}.png"
                    try:
                        page.screenshot(path=shot, full_page=True)
                    except:
                        pass
                    print(f"  [SKIP] page={page_no} i={i} bp_left={bp_left} err={str(e)[:180]} screenshot={shot}")
                
                jitter_sleep(ROW_SLEEP_RANGE)

            next_btn = page.get_by_role("link", name="Next")
            if next_btn.count() == 0:
                print("no Next, end。")
                break

            next_btn.click()
            page.wait_for_timeout(350)

            try:
                page.wait_for_function(
                    """(prev) => {
                        const links = Array.from(document.querySelectorAll("a"));
                        const texts = links.map(a => (a.innerText||"").trim());
                        const cur = texts.find(t => /^\\d+\\/\\d+$/.test(t)) || "";
                        return cur && cur !== prev;
                    }""",
                    arg=first_bp_before,
                    timeout=NEXT_TIMEOUT_MS
                )
            except Exception:
                print("Next-> no responds -> last page? -> end")
                break

            page_no += 1
            jitter_sleep(PAGE_SLEEP_RANGE)
            
        with open(OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["book_page", "date", "street_number", "street_name", "consideration"])
            w.writerows(rows_out)

        print(f"DONE -> {OUT} rows={len(rows_out)} unique={len(seen)}")
        browser.close()

if __name__ == "__main__":
    main()
