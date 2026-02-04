-- CrewAI Database Initialization Script
-- This script creates the necessary database structures for CrewAI applications

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS crewai;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set search path
SET search_path TO crewai, public;

-- Crews table
CREATE TABLE IF NOT EXISTS crews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    process_type VARCHAR(50) DEFAULT 'sequential',
    verbose BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    goal TEXT NOT NULL,
    backstory TEXT,
    verbose BOOLEAN DEFAULT false,
    allow_delegation BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    expected_output TEXT,
    agent_id UUID REFERENCES agents(id),
    crew_id UUID REFERENCES crews(id),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Crew executions table
CREATE TABLE IF NOT EXISTS crew_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crew_id UUID REFERENCES crews(id) NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    result JSONB,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Task executions table
CREATE TABLE IF NOT EXISTS task_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) NOT NULL,
    crew_execution_id UUID REFERENCES crew_executions(id) NOT NULL,
    agent_id UUID REFERENCES agents(id) NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    output TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Tool usage tracking table
CREATE TABLE IF NOT EXISTS tool_usages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_execution_id UUID REFERENCES task_executions(id),
    tool_name VARCHAR(255) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analytics schema tables
SET search_path TO analytics, public;

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL,
    metric_unit VARCHAR(50),
    dimensions JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cost tracking table
CREATE TABLE IF NOT EXISTS cost_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
SET search_path TO crewai, public;

CREATE INDEX IF NOT EXISTS idx_crews_created_at ON crews(created_at);
CREATE INDEX IF NOT EXISTS idx_agents_role ON agents(role);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status);
CREATE INDEX IF NOT EXISTS idx_crew_executions_status ON crew_executions(status);
CREATE INDEX IF NOT EXISTS idx_tool_usages_tool_name ON tool_usages(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_usages_timestamp ON tool_usages(timestamp);

SET search_path TO analytics, public;

CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_timestamp ON performance_metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_operation_timestamp ON cost_tracking(operation, timestamp);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables that have updated_at columns
SET search_path TO crewai, public;

CREATE TRIGGER update_crews_updated_at BEFORE UPDATE ON crews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO crews (name, description, process_type) VALUES
    ('AI Research Crew', 'A crew specialized in AI research and analysis', 'sequential'),
    ('Content Creation Crew', 'A crew for creating high-quality content', 'hierarchical')
ON CONFLICT DO NOTHING;

INSERT INTO agents (name, role, goal, backstory) VALUES
    ('Research Assistant', 'Senior Research Analyst', 'Conduct thorough research on AI topics', 'An experienced researcher with expertise in AI and machine learning'),
    ('Content Writer', 'Tech Content Strategist', 'Create engaging technical content', 'A skilled writer who specializes in making complex topics accessible'),
    ('Editor', 'Chief Editor', 'Review and polish content for publication', 'A meticulous editor with years of experience in technical publishing')
ON CONFLICT DO NOTHING;