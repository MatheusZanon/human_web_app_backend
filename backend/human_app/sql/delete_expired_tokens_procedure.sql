DELIMITER //

CREATE PROCEDURE delete_expired_tokens()
BEGIN
	DELETE FROM password_reset WHERE expires_in < NOW();
END //

DELIMITER ;