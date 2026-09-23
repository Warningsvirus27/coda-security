import React, { useState } from 'react';
import ApiClient from '../services/api';

export default function AuthModal({ show, onClose, onAuthSuccess }) {
  const [tab, setTab] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!show) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let res;
      if (tab === 'login') {
        res = await ApiClient.login(username || email, password);
      } else {
        res = await ApiClient.register({
          username,
          email,
          password,
          first_name: firstName,
          last_name: lastName,
        });
      }

      if (res && res.authenticated) {
        onAuthSuccess(res.user);
        onClose();
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSSO = async () => {
    setError('');
    setLoading(true);
    try {
      const demoEmail = email || 'security.lead@metronlabs.com';
      const demoName = firstName ? `${firstName} ${lastName}` : 'Security Analyst';
      const res = await ApiClient.googleSSO(demoEmail, demoName, 'g_oauth2_mock_id_9901');
      if (res && res.authenticated) {
        onAuthSuccess(res.user);
        onClose();
      }
    } catch (err) {
      setError(err.message || 'Google SSO verification failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content shadow border-0">
          <div className="modal-header bg-dark text-white">
            <h5 className="modal-title d-flex align-items-center gap-2">
              <i className="bi bi-person-badge-fill text-warning"></i>
              {tab === 'login' ? 'Account Sign In' : 'Create New Account'}
            </h5>
            <button type="button" className="btn-close btn-close-white" onClick={onClose}></button>
          </div>

          <div className="modal-body p-4">
            {error && <div className="alert alert-danger py-2">{error}</div>}

            {/* Google SSO Button */}
            <div className="mb-3 text-center">
              <button
                type="button"
                className="btn btn-outline-dark w-100 d-flex align-items-center justify-content-center gap-2 py-2"
                onClick={handleGoogleSSO}
                disabled={loading}
              >
                <i className="bi bi-google text-danger fs-5"></i>
                <span className="fw-semibold">Sign in with Google SSO</span>
              </button>
              <div className="position-relative my-3">
                <hr />
                <span className="position-absolute top-50 start-50 translate-middle bg-white px-2 text-muted small">
                  or continue with email
                </span>
              </div>
            </div>

            {/* Tabs */}
            <ul className="nav nav-pills nav-fill mb-3">
              <li className="nav-item">
                <button
                  className={`nav-link ${tab === 'login' ? 'active' : ''}`}
                  onClick={() => { setTab('login'); setError(''); }}
                  type="button"
                >
                  Sign In
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${tab === 'register' ? 'active' : ''}`}
                  onClick={() => { setTab('register'); setError(''); }}
                  type="button"
                >
                  Sign Up
                </button>
              </li>
            </ul>

            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label small fw-bold">Username or Email</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. analyst1 or user@example.com"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>

              {tab === 'register' && (
                <>
                  <div className="mb-3">
                    <label className="form-label small fw-bold">Email Address</label>
                    <input
                      type="email"
                      className="form-control"
                      placeholder="user@company.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="row g-2 mb-3">
                    <div className="col">
                      <label className="form-label small fw-bold">First Name</label>
                      <input
                        type="text"
                        className="form-control"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                      />
                    </div>
                    <div className="col">
                      <label className="form-label small fw-bold">Last Name</label>
                      <input
                        type="text"
                        className="form-control"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                      />
                    </div>
                  </div>
                </>
              )}

              <div className="mb-3">
                <label className="form-label small fw-bold">Password</label>
                <input
                  type="password"
                  className="form-control"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary w-100 py-2 fw-semibold" disabled={loading}>
                {loading ? (
                  <span className="spinner-border spinner-border-sm me-2"></span>
                ) : null}
                {tab === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
