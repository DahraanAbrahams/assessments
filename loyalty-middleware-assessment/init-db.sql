-- Grant testuser full privileges on all DBs (including CREATE/DROP test DBs)
GRANT ALL PRIVILEGES ON *.* TO 'testuser'@'%';
FLUSH PRIVILEGES;