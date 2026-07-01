import { useState, useEffect, useMemo } from "react";
import { goalApi } from "../api";
import "./TeamMetricsView.css";

const PHASE_COLORS = {
  "reality-emulation": "#8b5cf6",
  "concurrent-engineering": "#3b82f6",
  "collective-intelligence": "#10b981",
  "contextual-intelligence": "#fbbf24",
  "continuous-intelligence": "#f59e0b",
  "perpetual-wisdom": "#ec4899"
};

const PHASE_LABELS = {
  "reality-emulation": "Reality Emulation",
  "concurrent-engineering": "Concurrent Engineering",
  "collective-intelligence": "Collective Intelligence",
  "contextual-intelligence": "Contextual Intelligence",
  "continuous-intelligence": "Continuous Intelligence",
  "perpetual-wisdom": "Perpetual Wisdom"
};

export const TeamMetricsView = ({ userId }) => {
  const [metrics, setMetrics] = useState(null);
  const [usersMap, setUsersMap] = useState({});
  const [inactiveThresholdDays, setInactiveThresholdDays] = useState(3);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortField, setSortField] = useState("signal_count");
  const [sortAsc, setSortAsc] = useState(false);

  const fetchMetricsAndUsers = async (threshold) => {
    try {
      setLoading(true);
      setError(null);
      
      const [metricsData, userMapping] = await Promise.all([
        goalApi.getTeamMetrics(threshold),
        goalApi.getUsersMap().catch(() => ({}))
      ]);

      setMetrics(metricsData);
      setUsersMap(userMapping || {});
    } catch (err) {
      console.error("Failed to load team metrics:", err);
      setError(err.message || "Failed to load team metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      fetchMetricsAndUsers(inactiveThresholdDays);
    }
  }, [userId, inactiveThresholdDays]);

  const handleSliderChange = (e) => {
    setInactiveThresholdDays(parseInt(e.target.value, 10));
  };

  const getUserName = (id) => {
    const user = usersMap[id];
    if (!user) return id;
    if (user.name && user.email) {
      return `${user.name} (${user.email})`;
    }
    return user.name || user.email || id;
  };

  const formatDate = (isoString) => {
    if (!isoString) return "—";
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return "—";
      return d.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return "—";
    }
  };

  const sortedVelocityList = useMemo(() => {
    if (!metrics || !metrics.per_user_velocity) return [];
    
    const list = Object.entries(metrics.per_user_velocity).map(([id, data]) => ({
      userId: id,
      name: getUserName(id),
      ...data
    }));

    return list.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (sortField === "last_active") {
        aVal = aVal ? new Date(aVal).getTime() : 0;
        bVal = bVal ? new Date(bVal).getTime() : 0;
      }

      if (aVal === bVal) return 0;
      const compare = aVal > bVal ? 1 : -1;
      return sortAsc ? compare : -compare;
    });
  }, [metrics, usersMap, sortField, sortAsc]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  if (loading && !metrics) {
    return (
      <div className="premium-card text-center" style={{ padding: "40px" }}>
        <div className="github-spinner" style={{ margin: "0 auto 16px" }}></div>
        <p style={{ color: "#9ca3af" }}>Loading team productivity analytics...</p>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="premium-card error-card">
        <div className="error-title">Failed to Load Metrics</div>
        <p className="error-text">{error}</p>
        <button className="retry-btn" onClick={() => fetchMetricsAndUsers(inactiveThresholdDays)}>
          Retry Loading
        </button>
      </div>
    );
  }

  const summary = metrics?.team_summary || {
    total_signals: 0,
    active_users: 0,
    inactive_users: 0,
    avg_signals_per_active_user: 0,
    total_pr_merges: 0,
    total_commits: 0
  };

  const goalsSummary = metrics?.goals_summary || {
    total_goals: 0,
    by_phase: {
      "reality-emulation": 0,
      "concurrent-engineering": 0,
      "collective-intelligence": 0,
      "contextual-intelligence": 0,
      "continuous-intelligence": 0,
      "perpetual-wisdom": 0
    }
  };

  const maxGoalCount = Math.max(...Object.values(goalsSummary.by_phase), 1);

  return (
    <div className="metrics-container">
      
      {/* Controls Card */}
      <div className="premium-card metrics-controls-card">
        <div className="metrics-title-group">
          <h2>📊 Team Analytics Dashboard</h2>
          <p>Real-time engineering activity velocity and goal progress metrics</p>
        </div>
        
        <div className="threshold-slider-group">
          <label htmlFor="inactive-slider">Inactivity Threshold:</label>
          <input
            id="inactive-slider"
            type="range"
            min="0"
            max="90"
            value={inactiveThresholdDays}
            onChange={handleSliderChange}
            className="threshold-slider"
          />
          <span className="threshold-value">{inactiveThresholdDays} days</span>
        </div>
      </div>

      {/* Stats Summary Grid */}
      <div className="metrics-summary-grid">
        <div className="premium-card metric-stat-card">
          <span className="metric-stat-label">Total Signals</span>
          <span className="metric-stat-value">{summary.total_signals}</span>
        </div>
        <div className="premium-card metric-stat-card active-users">
          <span className="metric-stat-label">Active Users</span>
          <span className="metric-stat-value">{summary.active_users}</span>
        </div>
        <div className="premium-card metric-stat-card inactive-users">
          <span className="metric-stat-label">Inactive Users</span>
          <span className="metric-stat-value">{summary.inactive_users}</span>
        </div>
        <div className="premium-card metric-stat-card avg-velocity">
          <span className="metric-stat-label">Avg Signals / User</span>
          <span className="metric-stat-value">
            {Number(summary.avg_signals_per_active_user).toFixed(1)}
          </span>
        </div>
        <div className="premium-card metric-stat-card pr-merges">
          <span className="metric-stat-label">PR Merges</span>
          <span className="metric-stat-value">{summary.total_pr_merges}</span>
        </div>
        <div className="premium-card metric-stat-card commits">
          <span className="metric-stat-label">Commits</span>
          <span className="metric-stat-value">{summary.total_commits}</span>
        </div>
      </div>

      {/* Main Content Columns */}
      <div className="metrics-columns-row">
        
        {/* Left Column: Team Velocity List */}
        <div className="premium-card team-table-card">
          <div className="card-header-with-actions">
            <h3>🏃 Engineering Velocity</h3>
          </div>
          
          <div className="table-responsive">
            <table className="metrics-table">
              <thead>
                <tr>
                  <th onClick={() => handleSort("name")}>
                    Member {sortField === "name" && (sortAsc ? "▲" : "▼")}
                  </th>
                  <th onClick={() => handleSort("signal_count")}>
                    Signals {sortField === "signal_count" && (sortAsc ? "▲" : "▼")}
                  </th>
                  <th onClick={() => handleSort("pr_merges")}>
                    PRs {sortField === "pr_merges" && (sortAsc ? "▲" : "▼")}
                  </th>
                  <th onClick={() => handleSort("commits")}>
                    Commits {sortField === "commits" && (sortAsc ? "▲" : "▼")}
                  </th>
                  <th onClick={() => handleSort("goal_advances")}>
                    Advances {sortField === "goal_advances" && (sortAsc ? "▲" : "▼")}
                  </th>
                  <th onClick={() => handleSort("last_active")}>
                    Last Active {sortField === "last_active" && (sortAsc ? "▲" : "▼")}
                  </th>
                  <th>Streams</th>
                </tr>
              </thead>
              <tbody>
                {sortedVelocityList.map((row) => (
                  <tr key={row.userId}>
                    <td>
                      <div className="table-user-cell">
                        <span className="user-cell-name">{row.name}</span>
                        <span className="user-cell-id">{row.userId}</span>
                      </div>
                    </td>
                    <td style={{ fontWeight: 600 }}>{row.signal_count}</td>
                    <td>{row.pr_merges}</td>
                    <td>{row.commits}</td>
                    <td>{row.goal_advances}</td>
                    <td>{formatDate(row.last_active)}</td>
                    <td>
                      <div className="metrics-stream-chips">
                        {(row.streams || []).map((stream) => (
                          <span key={stream} className="stream-chip">
                            {stream}
                          </span>
                        ))}
                        {(!row.streams || row.streams.length === 0) && (
                          <span style={{ color: "#6b7280", fontSize: "0.75rem" }}>—</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {sortedVelocityList.length === 0 && (
                  <tr>
                    <td colSpan="7" className="text-center" style={{ padding: "30px", color: "#9ca3af" }}>
                      No active engineers found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Inactive Users & SMILE Phase Distribution */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          
          {/* Needs Attention Card */}
          <div className="premium-card inactive-list-card">
            <h3>⚠️ Needs Attention</h3>
            <div className="inactive-list">
              {(metrics?.inactive_users || []).map((row) => (
                <div key={row.user_id} className="inactive-user-item">
                  <div className="inactive-user-info">
                    <span className="inactive-user-name">{getUserName(row.user_id)}</span>
                    <span className="inactive-user-seen">Last seen: {formatDate(row.last_seen)}</span>
                  </div>
                  <span className={`inactive-days-badge ${row.days_inactive >= 7 ? "badge-danger-soft" : "badge-warning-soft"}`}>
                    {row.days_inactive}d inactive
                  </span>
                </div>
              ))}
              {(!metrics?.inactive_users || metrics.inactive_users.length === 0) && (
                <div className="empty-inactive-state">
                  <span className="empty-icon">🎉</span>
                  <span className="empty-text">Everyone has been active recently!</span>
                </div>
              )}
            </div>
          </div>

          {/* Goal Distribution Card */}
          <div className="premium-card goals-chart-card">
            <h3>🎯 Goal Distribution ({goalsSummary.total_goals})</h3>
            <div className="goals-distribution-list" style={{ marginTop: "16px" }}>
              {Object.entries(PHASE_LABELS).map(([phase, label]) => {
                const count = goalsSummary.by_phase[phase] || 0;
                const percentage = (count / maxGoalCount) * 100;
                const fillColor = PHASE_COLORS[phase];
                return (
                  <div key={phase} className="goals-dist-item">
                    <div className="goals-dist-label-row">
                      <span className="goals-dist-name">{label}</span>
                      <span className="goals-dist-count">{count}</span>
                    </div>
                    <div className="goals-dist-bar-bg">
                      <div
                        className="goals-dist-bar-fill"
                        style={{
                          width: `${percentage}%`,
                          backgroundColor: fillColor,
                          boxShadow: `0 0 8px ${fillColor}66`
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
