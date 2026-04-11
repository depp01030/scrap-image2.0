import { BaseHandler } from "./base-handler.js";

export class LoveMinuetHandler extends BaseHandler {
  canHandle(url) {
    return url.hostname === "en.love-minuet.com";
  }
}

