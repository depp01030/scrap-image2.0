const collectButton = document.getElementById("collect-button");
const statusBox = document.getElementById("status");

function setStatus(message, data = null) {
  statusBox.textContent = data
    ? `${message}\n\n${JSON.stringify(data, null, 2)}`
    : message;
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function scanActivePage(tabId) {
  return chrome.tabs.sendMessage(tabId, { type: "scan-product-page" });
}

async function submitPayload(payload) {
  return chrome.runtime.sendMessage({
    type: "collect-product-images",
    payload,
  });
}

collectButton.addEventListener("click", async () => {
  collectButton.disabled = true;
  setStatus("正在掃描頁面...");

  try {
    const tab = await getActiveTab();
    if (!tab?.id) {
      throw new Error("找不到目前的分頁");
    }

    const scanResult = await scanActivePage(tab.id);
    if (!scanResult?.success) {
      setStatus("目前頁面不在支援網站內，或尚未擷取到資料。", scanResult?.payload);
      return;
    }

    if (!Array.isArray(scanResult.payload.image_urls) || scanResult.payload.image_urls.length === 0) {
      setStatus("已辨識到支援網站，但目前沒有抓到任何圖片網址。", {
        site_code: scanResult.payload.site_code,
        page_url: scanResult.payload.page_url,
        metadata: scanResult.payload.metadata,
      });
      return;
    }

    setStatus("正在送到 local service...", {
      site_code: scanResult.payload.site_code,
      image_count: scanResult.payload.image_urls.length,
    });

    const response = await submitPayload(scanResult.payload);
    if (!response?.ok) {
      setStatus("local service 回傳失敗。", response?.data);
      return;
    }

    setStatus("送出成功。", response.data);
  } catch (error) {
    setStatus("流程失敗。", { message: error.message });
  } finally {
    collectButton.disabled = false;
  }
});
