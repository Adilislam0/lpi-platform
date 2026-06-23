import { useState, useEffect } from "react";
import { goalApi } from "../api";
import "./GithubTracker.css";
import { useToast } from "./Toast";

export const GithubTracker = ({ userId }) => {
  const { showToast } = useToast();
  const [isConnected, setIsConnected] = useState(false);
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [trackingStatus, setTrackingStatus] = useState({}); // { repoFullName: "success" | "error" | "loading" }

  const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID;

  const fetchRepositories = async () => {
    if (!userId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await goalApi.getGithubRepositories(userId);
      setRepos(data.repositories || []);
      setIsConnected(true);
    } catch (err) {
      console.warn("Failed to fetch GitHub repos (likely not connected yet):", err.message);
      setIsConnected(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepositories();
    if (userId) {
      const activeList = JSON.parse(localStorage.getItem(`tracked_repos_${userId}`) || "[]");
      const initialStatus = {};
      activeList.forEach((name) => {
        initialStatus[name] = "success";
      });
      setTrackingStatus(initialStatus);
    } else {
      setTrackingStatus({});
    }
  }, [userId]);

  const handleDisconnectAccount = async () => {
    if (!userId) return;
    try {
      setLoading(true);
      await goalApi.disconnectGithubAccount(userId);
      setIsConnected(false);
      setRepos([]);
      setTrackingStatus({});
      localStorage.removeItem(`tracked_repos_${userId}`);
      showToast("Successfully disconnected GitHub account.", "success");
    } catch (err) {
      console.error("Failed to disconnect account:", err);
      showToast(err.message || "Failed to disconnect GitHub account.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = () => {
    if (!clientId) {
      setError("VITE_GITHUB_CLIENT_ID is not configured in the environment.");
      return;
    }
    const redirectUri = window.location.origin;
    const scope = "repo,admin:repo_hook";
    const githubUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&scope=${scope}&redirect_uri=${redirectUri}&prompt=select_account`;
    window.location.href = githubUrl;
  };

  const handleTrackRepo = async (repo) => {
    if (!userId) return;
    setActionLoading(repo.full_name);
    setTrackingStatus((prev) => ({ ...prev, [repo.full_name]: "loading" }));
    try {
      const response = await goalApi.trackGithubRepository(userId, repo.owner, repo.name);
      setTrackingStatus((prev) => ({ ...prev, [repo.full_name]: "success" }));
      
      const storageKey = `tracked_repos_${userId}`;
      const activeList = JSON.parse(localStorage.getItem(storageKey) || "[]");
      if (!activeList.includes(repo.full_name)) {
        activeList.push(repo.full_name);
        localStorage.setItem(storageKey, JSON.stringify(activeList));
      }
    } catch (err) {
      console.error("Failed to track repository:", err);
      setTrackingStatus((prev) => ({ ...prev, [repo.full_name]: "error" }));
      setTimeout(() => {
        showToast(err.message || "Failed to set up tracking webhook.", "error");
      }, 50);
    } finally {
      setActionLoading(null);
    }
  };

  const handleUntrackRepo = async (repo) => {
    if (!userId) return;
    setActionLoading(repo.full_name);
    setTrackingStatus((prev) => ({ ...prev, [repo.full_name]: "loading" }));
    try {
      await goalApi.disconnectGithubRepository(userId, repo.owner, repo.name);
      setTrackingStatus((prev) => {
        const next = { ...prev };
        delete next[repo.full_name];
        return next;
      });
      
      const storageKey = `tracked_repos_${userId}`;
      const activeList = JSON.parse(localStorage.getItem(storageKey) || "[]");
      const filteredList = activeList.filter((name) => name !== repo.full_name);
      localStorage.setItem(storageKey, JSON.stringify(filteredList));
      showToast(`Successfully disconnected from ${repo.name}.`, "success");
    } catch (err) {
      console.error("Failed to disconnect repository:", err);
      showToast(err.message || "Failed to disconnect repository.", "error");
      setTrackingStatus((prev) => ({ ...prev, [repo.full_name]: "success" }));
    } finally {
      setActionLoading(null);
    }
  };

  const filteredRepos = repos.filter((repo) =>
    repo.full_name.toLowerCase().includes(searchTerm.toLowerCase()) &&
    repo.permissions?.admin === true
  );


  if (!userId) {
    return (
      <div className="premium-card github-container">
        <div className="empty-state">
          <h3>Authentication Required</h3>
          <p>Please log in to integrate your GitHub workspace.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="premium-card github-container">
      <div className="github-header-row">
        <div>
          <h2 className="widget-title" style={{ fontSize: "1.25rem", fontWeight: "700" }}>
            GitHub Activity Signals
          </h2>
          <p className="github-subtitle">
            Link your GitHub account to automatically ingest push & pull request events as LPI Activity Signals.
          </p>
        </div>
        {isConnected && (
          <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap", justifyContent: "flex-end" }}>
            {Object.keys(trackingStatus).filter(k => trackingStatus[k] === "success").length > 0 && (
              <div className="connection-badge tracked-repo" style={{ background: "rgba(139, 92, 246, 0.1)", color: "#a78bfa", border: "1px solid rgba(139, 92, 246, 0.2)", textTransform: "none", letterSpacing: "normal" }}>
                Active: {Object.keys(trackingStatus).filter(k => trackingStatus[k] === "success").join(", ")}
              </div>
            )}
            <div className="connection-badge connected">
              <span className="dot"></span> Connected
            </div>
            <button
              className="github-track-btn tracking untrack-btn"
              onClick={handleDisconnectAccount}
              style={{
                background: "rgba(239, 68, 68, 0.15)",
                borderColor: "#ef4444",
                color: "#ef4444",
                padding: "4px 10px",
                fontSize: "0.75rem",
                borderRadius: "30px",
                margin: 0
              }}
            >
              Disconnect Account
            </button>
          </div>
        )}
      </div>


      {error && <div className="github-error-banner">{error}</div>}

      {loading ? (
        <div className="github-loading">
          <div className="github-spinner"></div>
          <p>Loading GitHub integration...</p>
        </div>
      ) : !isConnected ? (
        <div className="github-connect-flow">
          <div className="github-auth-card">
            <div className="github-large-icon">🐙</div>
            <h3>Connect Your GitHub Account</h3>
            <p>
              Grant the platform secure access to list your repositories and configure webhooks to feed your activity signals timeline.
            </p>
            <button className="github-auth-btn" onClick={handleConnect}>
              Authorize with GitHub
            </button>
          </div>
        </div>
      ) : (
        <div className="github-repos-dashboard">
          <div className="github-toolbar">
            <input
              type="text"
              placeholder="Search repositories..."
              className="github-search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <button className="github-refresh-btn" onClick={fetchRepositories} title="Refresh repositories">
              ⟳ Refresh
            </button>
          </div>

          <div className="github-repo-list">
            {filteredRepos.length === 0 ? (
              <div className="empty-state">
                <p>No repositories found.</p>
              </div>
            ) : (
              filteredRepos.map((repo) => {
                const status = trackingStatus[repo.full_name];
                return (
                  <div key={repo.id} className="github-repo-card">
                    <div className="github-repo-info">
                      <h4 className="github-repo-name">
                        <a href={repo.html_url} target="_blank" rel="noopener noreferrer">
                          {repo.full_name}
                        </a>
                      </h4>
                      <div className="github-repo-badges">
                        {repo.private ? (
                          <span className="repo-badge private">Private</span>
                        ) : (
                          <span className="repo-badge public">Public</span>
                        )}
                      </div>
                    </div>

                    {status === "success" ? (
                      <button
                        className="github-track-btn tracking untrack-btn"
                        onClick={() => handleUntrackRepo(repo)}
                        disabled={actionLoading === repo.full_name}
                        style={{ background: "rgba(239, 68, 68, 0.15)", borderColor: "#ef4444", color: "#ef4444" }}
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        className="github-track-btn"
                        onClick={() => handleTrackRepo(repo)}
                        disabled={actionLoading === repo.full_name}
                      >
                        {actionLoading === repo.full_name ? (
                          <>
                            <span className="button-spinner"></span> Creating Webhook...
                          </>
                        ) : (
                          "🔗 Track Repository"
                        )}
                      </button>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};
