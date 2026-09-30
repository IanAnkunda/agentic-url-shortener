CREATE TABLE short_urls (
    id UUID PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    original_url VARCHAR(2048) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NULL,
    click_count BIGINT NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE NULL
);
CREATE UNIQUE INDEX idx_short_urls_code ON short_urls(code);
