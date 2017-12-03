# Trigger for determining when player was last active
DELIMITER $$
CREATE TRIGGER on_player_action
    BEFORE UPDATE ON players
    FOR EACH ROW
BEGIN
    IF OLD.actions > NEW.actions THEN
    SET NEW.last_active = NOW();
END IF;
END$$
DELIMITER ;
