package com.example.shortener.dto;

import java.time.Instant;

public record CreateShortUrlResponse(String code, String shortUrl, String originalUrl, Instant expiresAt) {}
