package com.example.shortener.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.hibernate.validator.constraints.URL;

public record CreateShortUrlRequest(
        @URL(protocol = "https", message = "url must be a valid HTTPS URL")
        @Size(max = 2048)
        String url,

        @Pattern(regexp = "^[A-Za-z0-9_-]{4,32}$", message = "customAlias must be 4-32 URL-safe characters")
        String customAlias,

        @Min(value = 60, message = "ttlSeconds must be at least 60")
        Long ttlSeconds
) {}
