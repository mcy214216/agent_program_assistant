CREATE TABLE IF NOT EXISTS agentmessages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id VARCHAR(64) NOT NULL,          -- 会话唯一标识（可由前端提供或自动生成）
    role ENUM('system', 'user', 'assistant', 'tool') NOT NULL,
    content TEXT,                                   -- 消息内容
    tool_calls JSON,                                -- assistant 的工具调用请求（JSON 数组）
    tool_call_id VARCHAR(64),                       -- tool 消息对应的调用 ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conversation (conversation_id),
    INDEX idx_created (created_at)
);
use agenthistorl;
SHOW TABLES;
DESCRIBE agentmessages;
# DROP TABLE conversation_messages;
select * from agentmessages;