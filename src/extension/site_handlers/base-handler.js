export class BaseHandler {
  canHandle(_url, _document) {
    return false;
  }

  extractImages(_document) {
    return [];
  }

  extractProductInfo(_document) {
    return {};
  }
}

