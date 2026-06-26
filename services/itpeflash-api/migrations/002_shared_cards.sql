CREATE TABLE IF NOT EXISTS itpeflash_shared_cards (
    share_id TEXT PRIMARY KEY,
    owner_user_id UUID NOT NULL REFERENCES itpeflash_accounts(user_id) ON DELETE RESTRICT,
    note_data JSONB NOT NULL CHECK (jsonb_typeof(note_data) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS itpeflash_shared_cards_owner_idx
    ON itpeflash_shared_cards(owner_user_id, created_at DESC);
