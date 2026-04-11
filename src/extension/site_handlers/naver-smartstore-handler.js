import { BaseHandler } from "./base-handler.js";

export class NaverSmartstoreHandler extends BaseHandler {
  canHandle(url) {
    return url.hostname === "smartstore.naver.com" && /\/products\/\d+/.test(url.pathname);
  }
}
