import requests
import time
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

def audit_website(url, timeout=7):
    if not url or url.strip() == "":
        return {
            "has_viewport": False,
            "http_status": 0,
            "load_speed_sec": 0.0,
            "is_broken_mobile": True,
            "reason": "No Website URL Provided"
        }

    formatted_url = url.strip()
    if not formatted_url.startswith("http://") and not formatted_url.startswith("https://"):
        formatted_url = "https://" + formatted_url

    start_time = time.time()
    try:
        response = requests.get(formatted_url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        load_time = round(time.time() - start_time, 2)
        http_status = response.status_code

        if http_status != 200:
            return {
                "has_viewport": False,
                "http_status": http_status,
                "load_speed_sec": load_time,
                "is_broken_mobile": True,
                "reason": f"HTTP Error Status {http_status}"
            }

        soup = BeautifulSoup(response.text, "html.parser")
        viewport_meta = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "viewport"})
        has_viewport = bool(viewport_meta)

        # Flagged as broken/missing mobile if missing viewport tag OR page load takes > 4 seconds
        is_broken = (not has_viewport) or (load_time > 4.0)

        reason_parts = []
        if not has_viewport:
            reason_parts.append("Missing Mobile Viewport Meta Tag")
        if load_time > 4.0:
            reason_parts.append(f"Slow Load Speed ({load_time}s)")

        return {
            "has_viewport": has_viewport,
            "http_status": http_status,
            "load_speed_sec": load_time,
            "is_broken_mobile": is_broken,
            "reason": ", ".join(reason_parts) if reason_parts else "Mobile Ready"
        }

    except requests.exceptions.Timeout:
        return {
            "has_viewport": False,
            "http_status": 408,
            "load_speed_sec": timeout,
            "is_broken_mobile": True,
            "reason": "Connection Timeout"
        }
    except Exception as e:
        return {
            "has_viewport": False,
            "http_status": 500,
            "load_speed_sec": round(time.time() - start_time, 2),
            "is_broken_mobile": True,
            "reason": f"Connection Failed ({str(e)})"
        }

if __name__ == "__main__":
    test_result = audit_website("https://example.com")
    print("Test audit result:", test_result)
