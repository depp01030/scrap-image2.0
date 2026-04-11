export function buildPayload({
  siteCode,
  pageUrl,
  productId = null,
  productName = null,
  imageUrls = [],
  metadata = {},
}) {
  return {
    site_code: siteCode,
    page_url: pageUrl,
    product_id: productId,
    product_name: productName,
    image_urls: imageUrls,
    metadata,
  };
}

