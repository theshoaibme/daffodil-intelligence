"""
Daffodil Intelligence - System Health Dashboard
Real-time monitoring for production deployment
"""

from flask import Flask, jsonify, render_template_string
import psutil
import time
from datetime import datetime
import threading

app = Flask(__name__)

# Metrics storage
class MetricsStore:
    def __init__(self):
        self.requests = 0
        self.errors = 0
        self.ws_connections = 0
        self.agent_calls = {"academic": 0, "library": 0, "career": 0, "campus": 0, "research": 0, "coding": 0}
        self.tool_calls = {}
        self.start_time = time.time()
        self.ai_latency = []
        self.hallucination_count = 0
    
    def record_request(self):
        self.requests += 1
    
    def record_error(self):
        self.errors += 1
    
    def record_agent(self, agent_name):
        if agent_name in self.agent_calls:
            self.agent_calls[agent_name] += 1
    
    def record_tool(self, tool_name):
        self.tool_calls[tool_name] = self.tool_calls.get(tool_name, 0) + 1
    
    def record_ai_latency(self, latency_ms):
        self.ai_latency.append(latency_ms)
        if len(self.ai_latency) > 100:
            self.ai_latency = self.ai_latency[-100:]
    
    def get_avg_latency(self):
        return sum(self.ai_latency) / len(self.ai_latency) if self.ai_latency else 0

metrics = MetricsStore()

# HTML Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>DI - System Health Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .header h1 { color: #22d3ee; font-size: 28px; }
        .status { display: inline-block; padding: 6px 16px; border-radius: 20px; background: #22c55e; color: white; font-weight: 600; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; }
        .card h3 { color: #94a3b8; font-size: 14px; text-transform: uppercase; margin-bottom: 16px; }
        .card .value { font-size: 36px; font-weight: 700; color: #22d3ee; }
        .card .sub { color: #64748b; font-size: 14px; margin-top: 8px; }
        
        .section { margin-bottom: 30px; }
        .section h2 { color: #e2e8f0; font-size: 20px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #334155; }
        
        .agent-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
        .agent-item { background: #334155; padding: 16px; border-radius: 8px; text-align: center; }
        .agent-item .name { color: #94a3b8; font-size: 12px; }
        .agent-item .count { color: #22d3ee; font-size: 24px; font-weight: 600; }
        
        .tools-grid { display: flex; flex-wrap: wrap; gap: 8px; }
        .tool-tag { background: #334155; padding: 8px 16px; border-radius: 20px; font-size: 13px; }
        .tool-tag .count { color: #22d3ee; margin-left: 8px; font-weight: 600; }
        
        .latency-bar { height: 8px; background: #334155; border-radius: 4px; overflow: hidden; margin-top: 12px; }
        .latency-fill { height: 100%; background: #22c55e; transition: width 0.3s; }
        
        .alert { background: #dc2626; color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px; display: none; }
        
        .refresh { text-align: center; margin-top: 20px; color: #64748b; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🟣 Daffodil Intelligence - System Health</h1>
        <span class="status">● All Systems Operational</span>
    </div>
    
    <div class="alert" id="alert"></div>
    
    <div class="grid">
        <div class="card">
            <h3>Total Requests</h3>
            <div class="value">{{ metrics.requests }}</div>
            <div class="sub">Since {{ uptime }}</div>
        </div>
        <div class="card">
            <h3>Error Rate</h3>
            <div class="value">{{ "%.1f"|format(error_rate) }}%</div>
            <div class="sub">{{ metrics.errors }} errors</div>
        </div>
        <div class="card">
            <h3>AI Latency</h3>
            <div class="value">{{ "%.0f"|format(avg_latency) }}ms</div>
            <div class="sub">Average response time</div>
            <div class="latency-bar"><div class="latency-fill" style="width: {{ min(avg_latency / 500 * 100, 100) }}%"></div></div>
        </div>
        <div class="card">
            <h3>WebSocket Connections</h3>
            <div class="value">{{ metrics.ws_connections }}</div>
            <div class="sub">Active users</div>
        </div>
    </div>
    
    <div class="section">
        <h2>🤖 Agent Activity</h2>
        <div class="agent-grid">
            {% for agent, count in metrics.agent_calls.items() %}
            <div class="agent-item">
                <div class="name">{{ agent.title() }}</div>
                <div class="count">{{ count }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="section">
        <h2>🔧 Tool Calls</h2>
        <div class="tools-grid">
            {% for tool, count in metrics.tool_calls.items() %}
            <div class="tool-tag">{{ tool }}<span class="count">{{ count }}</span></div>
            {% endfor %}
            {% if not metrics.tool_calls %}
            <div class="tool-tag">No tool calls yet</div>
            {% endif %}
        </div>
    </div>
    
    <div class="section">
        <h2>📊 System Resources</h2>
        <div class="grid">
            <div class="card">
                <h3>CPU Usage</h3>
                <div class="value">{{ "%.1f"|format(cpu) }}%</div>
            </div>
            <div class="card">
                <h3>Memory Usage</h3>
                <div class="value">{{ "%.1f"|format(memory) }}%</div>
            </div>
            <div class="card">
                <h3>Disk Usage</h3>
                <div class="value">{{ "%.1f"|format(disk) }}%</div>
            </div>
        </div>
    </div>
    
    <div class="refresh">Auto-refreshes every 5 seconds</div>
    
    <script>
        setTimeout(() => location.reload(), 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    uptime_seconds = time.time() - metrics.start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    uptime = f"{hours}h {minutes}m"
    
    error_rate = (metrics.errors / metrics.requests * 100) if metrics.requests > 0 else 0
    avg_latency = metrics.get_avg_latency()
    
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    return render_template_string(DASHBOARD_HTML,
        metrics=metrics,
        uptime=uptime,
        error_rate=error_rate,
        avg_latency=avg_latency,
        cpu=cpu,
        memory=memory,
        disk=disk
    )

@app.route('/api/metrics')
def api_metrics():
    return jsonify({
        "requests": metrics.requests,
        "errors": metrics.errors,
        "error_rate": (metrics.errors / metrics.requests * 100) if metrics.requests > 0 else 0,
        "ws_connections": metrics.ws_connections,
        "agent_calls": metrics.agent_calls,
        "tool_calls": metrics.tool_calls,
        "avg_ai_latency_ms": metrics.get_avg_latency(),
        "uptime_seconds": time.time() - metrics.start_time,
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent
    })

@app.route('/api/record-request')
def record_request():
    metrics.record_request()
    return {"status": "ok"}

@app.route('/api/record-error')
def record_error():
    metrics.record_error()
    return {"status": "ok"}

@app.route('/api/record-agent/<agent_name>')
def record_agent(agent_name):
    metrics.record_agent(agent_name)
    return {"status": "ok"}

@app.route('/api/record-tool/<tool_name>')
def record_tool(tool_name):
    metrics.record_tool(tool_name)
    return {"status": "ok"}

if __name__ == '__main__':
    print("🚀 Starting DI System Health Dashboard on http://localhost:8002")
    app.run(host='0.0.0.0', port=8002, debug=True)