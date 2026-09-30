package com.example.shortener.service;

import com.example.shortener.dto.CreateShortUrlRequest;
import com.example.shortener.model.ShortUrl;
import com.example.shortener.repo.ShortUrlRepository;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.web.server.ResponseStatusException;

import java.security.SecureRandom;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class UrlShortenerServiceTest {
    private final ShortUrlRepository repository = mock(ShortUrlRepository.class);
    private final Clock clock = Clock.fixed(Instant.parse("2026-09-30T15:00:00Z"), ZoneOffset.UTC);
    private final UrlShortenerService service = new UrlShortenerService(repository, new SecureRandom(), clock);

    @Test
    void createsCustomAlias() {
        when(repository.existsByCode("demo1")).thenReturn(false);
        when(repository.save(any(ShortUrl.class))).thenAnswer(invocation -> invocation.getArgument(0));

        ShortUrl result = service.create(new CreateShortUrlRequest("https://example.com/path", "demo1", 3600L));

        assertEquals("demo1", result.getCode());
        assertEquals("https://example.com/path", result.getOriginalUrl());
        assertEquals(Instant.parse("2026-09-30T16:00:00Z"), result.getExpiresAt());
    }

    @Test
    void rejectsDuplicateAlias() {
        when(repository.existsByCode("demo1")).thenReturn(true);
        assertThrows(ResponseStatusException.class,
                () -> service.create(new CreateShortUrlRequest("https://example.com", "demo1", null)));
    }

    @Test
    void expiredLinkReturnsGone() {
        ShortUrl expired = new ShortUrl(UUID.randomUUID(), "old1", "https://example.com",
                Instant.parse("2026-09-30T13:00:00Z"), Instant.parse("2026-09-30T14:00:00Z"));
        when(repository.findByCode("old1")).thenReturn(Optional.of(expired));
        assertThrows(ResponseStatusException.class, () -> service.resolve("old1"));
        verify(repository, never()).incrementClick(any(), any());
    }
}
