CREATE EVENT delete_expired_tokens_event
ON SCHEDULE EVERY 1 hour
DO
CALL delete_expired_tokens()