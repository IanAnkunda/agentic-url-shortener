package com.example.shortener.service;

import com.example.shortener.dto.AnalyticsResponse;
import com.example.shortener.dto.CreateShortUrlRequest;
import com.example.shortener.model.ShortUrl;
import com.example.shortener.repo.ShortUrlRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.security.SecureRandom;
import java.time.Clock;
import java.time.Instant;
import java.util.UUID;

@Service
public class UrlShortenerService {
    private static final char[] ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz".toCharArray();
    private static final int GENERATED_CODE_LENGTH = 7;
    private static final int MAX_COLLISION_RETRIES = 5;

    private final ShortUrlRepository repository;
    private final SecureRandom random;
    private final Clock clock;

    public UrlShortenerService(ShortUrlRepository repository) {
        this(repository, new SecureRandom(), Clock.systemUTC());
    }

    UrlShortenerService(ShortUrlRepository repository, SecureRandom random, Clock clock) {
        this.repository = repository;
        this.random = random;
        this.clock = clock;
    }

    @Transactional
    public ShortUrl create(CreateShortUrlRequest request) {
        if (request.url() == null || request.url().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "url is required");
        }

        Instant now = clock.instant();
        Instant expiresAt = request.ttlSeconds() == null ? null : now.plusSeconds(request.ttlSeconds());
        String code = request.customAlias() == null || request.customAlias().isBlank()
                ? nextUniqueCode()
                : reserveCustomAlias(request.customAlias());

        return repository.save(new ShortUrl(UUID.randomUUID(), code, request.url(), now, expiresAt));
    }

    @Transactional
    public String resolve(String code) {
        ShortUrl shortUrl = find(code);
        if (shortUrl.getExpiresAt() != null && !shortUrl.getExpiresAt().isAfter(clock.instant())) {
            throw new ResponseStatusException(HttpStatus.GONE, "short URL has expired");
        }
        repository.incrementClick(shortUrl.getId(), clock.instant());
        return shortUrl.getOriginalUrl();
    }

    @Transactional(readOnly = true)
    public AnalyticsResponse analytics(String code) {
        ShortUrl shortUrl = find(code);
        return new AnalyticsResponse(shortUrl.getCode(), shortUrl.getOriginalUrl(), shortUrl.getClickCount(),
                shortUrl.getCreatedAt(), shortUrl.getExpiresAt(), shortUrl.getLastAccessedAt());
    }

    @Transactional
    public void delete(String code) {
        repository.delete(find(code));
    }

    private ShortUrl find(String code) {
        return repository.findByCode(code)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "short URL not found"));
    }

    private String reserveCustomAlias(String alias) {
        if (repository.existsByCode(alias)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "custom alias already exists");
        }
        return alias;
    }

    private String nextUniqueCode() {
        for (int attempt = 0; attempt < MAX_COLLISION_RETRIES; attempt++) {
            String code = randomCode();
            if (!repository.existsByCode(code)) {
                return code;
            }
        }
        throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
                "unable to allocate a unique short code after bounded retries");
    }

    private String randomCode() {
        StringBuilder builder = new StringBuilder(GENERATED_CODE_LENGTH);
        for (int i = 0; i < GENERATED_CODE_LENGTH; i++) {
            builder.append(ALPHABET[random.nextInt(ALPHABET.length)]);
        }
        return builder.toString();
    }
}
