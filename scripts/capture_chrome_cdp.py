import base64
import json
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

import websocket


ROOT = Path.cwd()
OUT_DIR = ROOT / "reports" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PORT = 9223


def cdp_request(ws, method, params=None, msg_id=[0]):
    msg_id[0] += 1
    ws.send(json.dumps({"id": msg_id[0], "method": method, "params": params or {}}))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id[0]:
            return data


def wait_for_text(ws, text, timeout=45):
    end = time.time() + timeout
    expr = f"document.body && document.body.innerText.includes({json.dumps(text)})"
    while time.time() < end:
        result = cdp_request(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if result.get("result", {}).get("result", {}).get("value"):
            return True
        time.sleep(1)
    return False


def screenshot(ws, filename):
    result = cdp_request(
        ws,
        "Page.captureScreenshot",
        {"format": "png", "fromSurface": True},
    )
    data = base64.b64decode(result["result"]["data"])
    path = OUT_DIR / filename
    path.write_bytes(data)
    print(path)


def click_text(ws, text):
    expression = f"""
    (() => {{
      const target = [...document.querySelectorAll('*')].find(el =>
        el.innerText && el.innerText.trim().includes({json.dumps(text)}) &&
        (el.getAttribute('role') === 'tab' || el.tagName === 'BUTTON' || el.onclick || el.closest('[role=tab]'))
      );
      const el = target && (target.getAttribute('role') === 'tab' ? target : target.closest('[role=tab]') || target);
      if (el) {{ el.click(); return true; }}
      return false;
    }})()
    """
    return cdp_request(ws, "Runtime.evaluate", {"expression": expression, "returnByValue": True})


def main():
    profile = tempfile.mkdtemp(prefix="chrome-cdp-")
    proc = subprocess.Popen(
        [
            str(CHROME),
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={profile}",
            "--headless=new",
            "--disable-gpu",
            "--window-size=1440,1100",
            "http://localhost:8501",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        endpoint = None
        for _ in range(30):
            try:
                tabs = json.loads(urlopen(f"http://localhost:{PORT}/json").read().decode("utf-8"))
                endpoint = tabs[0]["webSocketDebuggerUrl"]
                break
            except Exception:
                time.sleep(1)
        if not endpoint:
            raise RuntimeError("Chrome CDP endpoint did not start")

        ws = websocket.create_connection(endpoint, timeout=10)
        cdp_request(ws, "Page.enable")
        cdp_request(ws, "Runtime.enable")
        cdp_request(ws, "Emulation.setDeviceMetricsOverride", {
            "width": 1440,
            "height": 1100,
            "deviceScaleFactor": 1,
            "mobile": False,
        })
        wait_for_text(ws, "企业客户流失", timeout=60)
        time.sleep(4)
        screenshot(ws, "01_streamlit_business_overview.png")

        tabs = [
            ("NLP", "02_streamlit_nlp.png"),
            ("聚类", "03_streamlit_cluster.png"),
            ("模型评估", "04_streamlit_model_metrics.png"),
            ("单客预测", "05_streamlit_single_customer_prediction.png"),
            ("输出图表", "06_streamlit_output_gallery.png"),
        ]
        for label, file_name in tabs:
            click_text(ws, label)
            time.sleep(3)
            screenshot(ws, file_name)
        ws.close()
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
