package com.example.shortener.repo;

import com.example.shortener.model.ShortUrl;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

public interface ShortUrlRepository extends JpaRepository<ShortUrl, UUID> {
    Optional<ShortUrl> findByCode(String code);
    boolean existsByCode(String code);

    /*
     * Concurrency Strategy: 
     * Executing an atomic UPDATE statement directly in the database avoids the 
     * classic read-modify-write race condition that occurs when fetching the entity 
     * into application memory under concurrent redirect traffic.
     */
    @Modifying
    @Transactional
    @Query("update ShortUrl s set s.clickCount = s.clickCount + 1, s.lastAccessedAt = :at where s.id = :id")
    int incrementClick(@Param("id") UUID id, @Param("at") Instant at);
}
