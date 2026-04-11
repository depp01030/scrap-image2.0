from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class JobRequest(BaseModel):
    site_code: str = Field(min_length=1)
    page_url: HttpUrl
    product_id: str | None = None
    product_name: str | None = None
    image_urls: list[HttpUrl] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, image_urls: list[HttpUrl]) -> list[HttpUrl]:
        unique_urls: list[HttpUrl] = []
        seen: set[str] = set()
        for url in image_urls:
            normalized = str(url)
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_urls.append(url)
        if not unique_urls:
            raise ValueError("image_urls must contain at least one URL")
        return unique_urls
