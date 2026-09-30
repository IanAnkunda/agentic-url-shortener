package com.example.shortener.dto;

import java.time.Instant;

public record AnalyticsResponse(String code, String originalUrl, long clicks, Instant createdAt,
                                Instant expiresAt, Instant lastAccessedAt) {}
