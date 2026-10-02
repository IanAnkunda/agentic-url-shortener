package com.example.shortener.controller;

import com.example.shortener.dto.AnalyticsResponse;
import com.example.shortener.dto.CreateShortUrlRequest;
import com.example.shortener.dto.CreateShortUrlResponse;
import com.example.shortener.model.ShortUrl;
import com.example.shortener.service.UrlShortenerService;
import jakarta.validation.Valid;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;

@RestController
public class UrlController {
    private final UrlShortenerService service;

    public UrlController(UrlShortenerService service) {
        this.service = service;
    }

    /*
     * Security Boundary: 
     * @Valid annotation triggers the JSR-380 constraints defined in 
     * CreateShortUrlRequest (e.g., HTTPS enforcement, length limits, regex 
     * patterns). Rejecting malformed payloads at the controller layer prevents 
     * downstream processing waste and mitigates injection risks.
     */
    @PostMapping("/api/v1/urls")
    public ResponseEntity<CreateShortUrlResponse> create(@Valid @RequestBody CreateShortUrlRequest request) {
        ShortUrl created = service.create(request);
        String shortUrl = ServletUriComponentsBuilder.fromCurrentContextPath()
                .pathSegment(created.getCode()).toUriString();
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new CreateShortUrlResponse(created.getCode(), shortUrl, created.getOriginalUrl(), created.getExpiresAt()));
    }

    @GetMapping("/{code:[A-Za-z0-9_-]{4,32}}")
    public ResponseEntity<Void> redirect(@PathVariable String code) {
        String target = service.resolve(code);
        return ResponseEntity.status(HttpStatus.FOUND)
                .header(HttpHeaders.LOCATION, URI.create(target).toString())
                .build();
    }

    @GetMapping("/api/v1/urls/{code}/analytics")
    public AnalyticsResponse analytics(@PathVariable String code) {
        return service.analytics(code);
    }

    @DeleteMapping("/api/v1/urls/{code}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable String code) {
        service.delete(code);
    }
}
