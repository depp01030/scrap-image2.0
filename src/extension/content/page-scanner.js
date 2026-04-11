(() => {
  function unblockRightClick() {
    const releaseEvent = (event) => {
      event.stopImmediatePropagation();
    };

    window.addEventListener("contextmenu", releaseEvent, true);
    window.addEventListener("selectstart", releaseEvent, true);
    window.addEventListener("dragstart", releaseEvent, true);

    const clearInlineHandlers = () => {
      const targets = [document, document.documentElement, document.body];
      for (const target of targets) {
        if (!target) {
          continue;
        }
        target.oncontextmenu = null;
        target.onselectstart = null;
        target.ondragstart = null;
      }
    };

    clearInlineHandlers();
    document.addEventListener("DOMContentLoaded", clearInlineHandlers, { once: true });
    window.setInterval(clearInlineHandlers, 1500);
  }

  function normalizeUrls(urls) {
    const seen = new Set();
    return urls
      .map((url) => {
        try {
          return new URL(url, window.location.href).href;
        } catch {
          return null;
        }
      })
      .filter((url) => url && !seen.has(url) && seen.add(url));
  }

  function getSiteCode() {
    const { hostname, pathname } = window.location;
    if (hostname === "en.love-minuet.com") {
      return "love_minuet";
    }
    if (hostname === "maybe-baby.co.kr" && pathname.includes("/product/")) {
      return "maybe_baby";
    }
    if (hostname === "www.veryyou.co.kr" && pathname.includes("/product/")) {
      return "veryyou";
    }
    if (hostname === "smartstore.naver.com" && /\/products\/\d+/.test(pathname)) {
      return "naver_smartstore";
    }
    return "unsupported";
  }

  function extractLoveMinuetImages() {
    const selectors = [
      "#prdDetail img",
      ".cont img",
      ".xans-product-additional img"
    ];
    const urls = selectors.flatMap((selector) =>
      Array.from(document.querySelectorAll(selector)).map(
        (img) => img.currentSrc || img.src || img.getAttribute("src") || ""
      )
    );

    return normalizeUrls(
      urls.filter((url) => url && !url.startsWith("data:image"))
    );
  }

  function extractCafe24DetailImages() {
    const selectors = [
      "#prdDetail img",
      ".cont img",
      ".prdDetail img",
      ".detailArea img",
      ".xans-product-additional img",
      "#contents img"
    ];

    const urls = selectors.flatMap((selector) =>
      Array.from(document.querySelectorAll(selector)).map((img) => {
        const anchor = img.closest("a");
        return (
          anchor?.href ||
          img.currentSrc ||
          img.src ||
          img.getAttribute("src") ||
          img.getAttribute("data-src") ||
          ""
        );
      })
    );

    return normalizeUrls(
      urls.filter((url) => {
        return (
          url &&
          !url.startsWith("data:image") &&
          !/icon|button|logo|banner|btn_|naver|translate/i.test(url)
        );
      })
    );
  }

  function extractNaverSmartstoreImages() {
    const containers = Array.from(document.querySelectorAll(".se-main-container"));
    const target =
      containers.length > 0
        ? containers.reduce((best, current) => {
            const bestCount = best.querySelectorAll("img").length;
            const currentCount = current.querySelectorAll("img").length;
            return currentCount > bestCount ? current : best;
          })
        : document;

    const collectedUrls = [];
    const seen = new Set();

    function addUrl(rawUrl) {
      if (!rawUrl || typeof rawUrl !== "string") {
        return;
      }

      const cleaned = rawUrl
        .replace(/_\d+x\d+\./i, ".")
        .replace(/\?type=[^#]+/i, "")
        .replace(/\?[^#]+$/i, "");

      if (
        !cleaned ||
        cleaned === "#" ||
        cleaned.startsWith("data:image") ||
        !/^https?:\/\//i.test(cleaned) ||
        !/shop-phinf|phinf|naver/i.test(cleaned) ||
        /icon|button|logo|badge|profile/i.test(cleaned) ||
        seen.has(cleaned)
      ) {
        return;
      }

      seen.add(cleaned);
      collectedUrls.push(cleaned);
    }

    target.querySelectorAll("a > img, img").forEach((img) => {
      const anchor = img.closest("a");
      const candidates = [
        anchor?.href,
        img.currentSrc,
        img.src,
        img.getAttribute("src"),
        img.getAttribute("data-src"),
        img.getAttribute("data-lazy-src"),
        img.dataset?.src,
        img.dataset?.lazySrc,
        img.dataset?.image,
      ];

      candidates.forEach(addUrl);
      Object.values(img.dataset || {}).forEach((value) => addUrl(value));
    });

    target.querySelectorAll("*").forEach((element) => {
      const backgroundImage = getComputedStyle(element).backgroundImage;
      const matchedUrl = backgroundImage.match(/url\(["']?(https?:\/\/[^"')]+)["']?\)/i);
      if (matchedUrl?.[1]) {
        addUrl(matchedUrl[1]);
      }
    });

    return normalizeUrls(collectedUrls);
  }

  function extractProductNameFromJsonLd() {
    const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
    for (const script of scripts) {
      try {
        const parsed = JSON.parse(script.textContent || "");
        const items = Array.isArray(parsed) ? parsed : [parsed];
        for (const item of items) {
          if (typeof item?.name === "string" && item.name.trim()) {
            return item.name.trim();
          }
        }
      } catch {
        continue;
      }
    }
    return "";
  }

  function extractProductNameFromScriptVar() {
    const scripts = Array.from(document.scripts);
    for (const script of scripts) {
      const text = script.textContent || "";
      const matched = text.match(/var\s+product_name\s*=\s*['"]([^'"]+)['"]\s*;/);
      if (matched?.[1]) {
        return matched[1].trim();
      }
    }
    return "";
  }

  function extractMetaKeywordsLead() {
    const meta = document.querySelector('meta[name="keywords"]');
    const content = meta?.getAttribute("content") || "";
    const first = content.split(",")[0]?.trim() || "";
    return first;
  }

  function getProductName(siteCode) {
    if (siteCode === "maybe_baby" || siteCode === "veryyou") {
      return (
        extractProductNameFromScriptVar() ||
        extractProductNameFromJsonLd() ||
        extractMetaKeywordsLead() ||
        document.title ||
        null
      );
    }

    if (siteCode === "naver_smartstore") {
      return extractProductNameFromJsonLd() || document.title || null;
    }

    return document.title || null;
  }

  function buildPayload() {
    const siteCode = getSiteCode();
    let imageUrls = [];

    if (siteCode === "love_minuet") {
      imageUrls = extractLoveMinuetImages();
    } else if (siteCode === "maybe_baby" || siteCode === "veryyou") {
      imageUrls = extractCafe24DetailImages();
    } else if (siteCode === "naver_smartstore") {
      imageUrls = extractNaverSmartstoreImages();
    }

    return {
      site_code: siteCode,
      page_url: window.location.href,
      product_id: window.location.pathname.split("/").filter(Boolean).pop() || null,
      product_name: getProductName(siteCode),
      image_urls: imageUrls,
      metadata: {
        captured_at: new Date().toISOString(),
        user_agent: navigator.userAgent,
        image_count: imageUrls.length,
        hostname: window.location.hostname,
        extractor_strategy:
          siteCode === "naver_smartstore"
            ? "largest-se-main-container"
            : siteCode === "maybe_baby" || siteCode === "veryyou"
              ? "cafe24-detail-selectors"
              : "default",
      },
    };
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type !== "scan-product-page") {
      return false;
    }

    const payload = buildPayload();
    sendResponse({
      success: payload.site_code !== "unsupported",
      payload,
    });
    return true;
  });

  unblockRightClick();
})();
