const CONTEXT_MENU_ID = "scrap-image2-context-download";
const LOCAL_SERVICE_URL = "http://127.0.0.1:8765/jobs";

function createContextMenu() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: CONTEXT_MENU_ID,
      title: "下載商品圖片",
      contexts: ["page", "image"],
      documentUrlPatterns: [
        "https://en.love-minuet.com/*",
        "https://smartstore.naver.com/*",
        "https://maybe-baby.co.kr/*",
        "https://www.veryyou.co.kr/*"
      ]
    });
  });
}

function showPageToast(tabId, message) {
  chrome.scripting.executeScript({
    target: { tabId },
    func: (toastMessage) => {
      const existing = document.getElementById("scrap-image2-toast");
      if (existing) {
        existing.remove();
      }

      const toast = document.createElement("div");
      toast.id = "scrap-image2-toast";
      toast.textContent = toastMessage;
      Object.assign(toast.style, {
        position: "fixed",
        top: "20px",
        right: "20px",
        zIndex: "2147483647",
        background: "rgba(21, 38, 33, 0.92)",
        color: "#fff",
        padding: "12px 14px",
        borderRadius: "10px",
        fontSize: "13px",
        fontFamily: "Segoe UI, sans-serif",
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.2)"
      });

      document.body.appendChild(toast);
      window.setTimeout(() => toast.remove(), 2600);
    },
    args: [message]
  });
}

chrome.runtime.onInstalled.addListener(() => {
  createContextMenu();
});

chrome.runtime.onStartup.addListener(() => {
  createContextMenu();
});

async function scanProductPage(tabId) {
  try {
    return await chrome.tabs.sendMessage(tabId, { type: "scan-product-page" });
  } catch (error) {
    if (!String(error?.message || "").includes("Receiving end does not exist")) {
      throw error;
    }

    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content/page-scanner.js"]
    });

    return chrome.tabs.sendMessage(tabId, { type: "scan-product-page" });
  }
}

async function submitPayload(payload) {
  const response = await fetch(LOCAL_SERVICE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  return { ok: response.ok, status: response.status, data };
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== CONTEXT_MENU_ID || !tab?.id) {
    return;
  }

  try {
    const scanResult = await scanProductPage(tab.id);
    if (!scanResult?.success) {
      showPageToast(tab.id, "目前頁面不支援，或沒有抓到頁面資料。");
      return;
    }

    if (!Array.isArray(scanResult.payload.image_urls) || scanResult.payload.image_urls.length === 0) {
      showPageToast(tab.id, `沒有抓到圖片。site=${scanResult.payload.site_code}`);
      return;
    }

    showPageToast(
      tab.id,
      `任務已送出，開始下載 ${scanResult.payload.image_urls.length} 張圖片...`
    );

    const response = await submitPayload(scanResult.payload);
    if (!response.ok) {
      showPageToast(tab.id, `local service 失敗：${response.data?.message || response.status}`);
      return;
    }

    showPageToast(
      tab.id,
      `下載完成。成功 ${response.data?.downloaded_count ?? 0} 張，失敗 ${response.data?.failed_count ?? 0} 張。job=${response.data?.job_id || "unknown"}`
    );
  } catch (error) {
    showPageToast(tab.id, `流程失敗：${error.message}`);
  }
});
