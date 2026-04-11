const API_URL = "http://127.0.0.1:8099/api";

// --- Theme Management ---
function initTheme() {
    const themeBtns = document.querySelectorAll('.theme-btn');
    const storedTheme = localStorage.getItem('sortedpc-theme') || 'system';
    
    setTheme(storedTheme);

    themeBtns.forEach(btn => {
        if (btn.getAttribute('data-theme-val') === storedTheme) {
            btn.classList.add('active');
        }
        btn.addEventListener('click', () => {
            themeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const val = btn.getAttribute('data-theme-val');
            setTheme(val);
        });
    });
}

function setTheme(val) {
    document.documentElement.setAttribute('data-theme', val);
    localStorage.setItem('sortedpc-theme', val);
}

// --- View Management ---
const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view');

navItems.forEach(item => {
    item.addEventListener('click', () => {
        navItems.forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        const targetId = item.getAttribute('data-target');
        views.forEach(view => {
            if(view.id === targetId) {
                view.classList.add('active');
                refreshView(targetId);
            } else {
                view.classList.remove('active');
            }
        });
    });
});

function refreshView(viewId) {
    if(viewId === 'destinations') fetchDestinations();
    if(viewId === 'history') fetchHistory();
    if(viewId === 'settings') fetchSettings();
}

// --- Toast Notifications ---
function showToast(message, type="info") {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- Global Status Polling ---
async function fetchStatus() {
    try {
        const res = await fetch(`${API_URL}/status`);
        const data = await res.json();
        
        const indicator = document.querySelector('.status-indicator');
        const title = document.querySelector('.status-title');
        const sub = document.querySelector('.status-sub');
        
        if (data.online) {
            indicator.classList.add('online');
            title.textContent = 'System Online';
            sub.textContent = 'Service running';
            document.getElementById('stat-state').textContent = 'Active';
            document.getElementById('stat-state').style.color = 'var(--success)';
        } else {
            indicator.classList.remove('online');
            title.textContent = 'System Offline';
            sub.textContent = 'Service inactive';
            document.getElementById('stat-state').textContent = 'Stopped';
            document.getElementById('stat-state').style.color = 'var(--danger)';
        }

        document.getElementById('stat-state-meta').textContent = data.registered ? 'Registered to Startup' : 'Not registered to Startup';
        document.getElementById('stat-hubs').textContent = data.total_destinations;
        
        // Show onboarding if no rules exist, exactly once per session
        if (!window.onboardingShown && data.watch_paths.length === 0 && data.total_destinations === 0) {
            document.getElementById('onboarding-modal').classList.add('active');
            window.onboardingShown = true;
        }
        
    } catch (e) {
        console.error("Backend offline", e);
    }
}

// --- Folder Pickers ---
async function pickFolderNative(inputId) {
    if (window.pywebview && window.pywebview.api) {
        const path = await window.pywebview.api.pick_folder();
        if (path) document.getElementById(inputId).value = path;
    } else {
        showToast("Native picker unavailable in browser environment.", "error");
    }
}

// Onboarding Picker
const obPickBtn = document.getElementById('btn-pick-ob-watch');
if (obPickBtn) obPickBtn.addEventListener('click', () => pickFolderNative('ob-watch-path'));

// Destination Picker
const destPickBtn = document.getElementById('btn-pick-dest-path');
if (destPickBtn) destPickBtn.addEventListener('click', () => pickFolderNative('dest-path'));

// Watch Path Picker
const watchPickBtn = document.getElementById('btn-pick-watch-path');
if (watchPickBtn) watchPickBtn.addEventListener('click', () => pickFolderNative('watch-path-input'));

// Onboarding Submit
const obSubmitBtn = document.getElementById('btn-submit-onboarding');
if (obSubmitBtn) {
    obSubmitBtn.addEventListener('click', async () => {
        const path = document.getElementById('ob-watch-path').value;
        if (!path) return showToast('Please select a folder to start.', 'error');
        
        // Add to watch paths
        const res = await fetch(`${API_URL}/watcher/paths`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path})
        });
        
        if (res.ok) {
            document.getElementById('onboarding-modal').classList.remove('active');
            showToast('Setup complete! Now add some destinations in the Knowledge Base.', 'success');
            // Navigate the user to destinations tab right away
            document.querySelector('.nav-item[data-target="destinations"]').click();
        } else {
            showToast('Failed to add watch path.', 'error');
        }
    });
}

// --- Watcher Controls ---
document.getElementById('btn-start-watcher').addEventListener('click', async () => {
    const res = await fetch(`${API_URL}/watcher/control?action=start`, {method: 'POST'});
    const data = await res.json();
    showToast(data.success ? 'Watcher started.' : 'Elevation failed or denied.', data.success ? 'success' : 'error');
    setTimeout(fetchStatus, 1500);
});

document.getElementById('btn-stop-watcher').addEventListener('click', async () => {
    const res = await fetch(`${API_URL}/watcher/control?action=stop`, {method: 'POST'});
    const data = await res.json();
    showToast(data.success ? 'Watcher stopped.' : 'Failed to stop watcher.', data.success ? 'info' : 'error');
    setTimeout(fetchStatus, 1500);
});

document.getElementById('btn-restart-watcher').addEventListener('click', async () => {
    showToast('Restarting watcher...');
    const res = await fetch(`${API_URL}/watcher/control?action=restart`, {method: 'POST'});
    const data = await res.json();
    showToast(data.success ? 'Watcher restarted.' : 'Restart failed.', data.success ? 'success' : 'error');
    setTimeout(fetchStatus, 1500);
});

document.getElementById('btn-register').addEventListener('click', async () => {
    await fetch(`${API_URL}/watcher/control?action=register`, {method: 'POST'});
    showToast('Task Registered', 'success');
    fetchStatus();
});

document.getElementById('btn-unregister').addEventListener('click', async () => {
    await fetch(`${API_URL}/watcher/control?action=unregister`, {method: 'POST'});
    showToast('Task Unregistered', 'info');
    fetchStatus();
});

// --- Manual Sort Modal ---
const sortModal = document.getElementById('sort-modal');
document.getElementById('btn-open-sort-modal').addEventListener('click', () => {
    sortModal.classList.add('active');
});

document.getElementById('btn-submit-sort').addEventListener('click', async () => {
    const path = document.getElementById('sort-target-path').value;
    sortModal.classList.remove('active');
    showToast('Priority sorting started in background...');
    await fetch(`${API_URL}/sort/manual`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({target_folder: path || null})
    });
});

// --- Destinations ---
const addForm = document.getElementById('dest-add-form');
document.getElementById('btn-add-dest').addEventListener('click', () => addForm.classList.remove('hidden'));
document.getElementById('btn-cancel-dest').addEventListener('click', () => addForm.classList.add('hidden'));

async function fetchDestinations() {
    const res = await fetch(`${API_URL}/knowledge/destinations`);
    const data = await res.json();
    const container = document.getElementById('destinations-list');
    container.innerHTML = '';
    
    if(data.length === 0) {
        container.innerHTML = '<p class="text-muted">No folders mapped.</p>';
        return;
    }
    
    data.forEach(d => {
        const card = document.createElement('div');
        card.className = 'hub-card panel';
        card.innerHTML = `
            <div class="hub-path">${d.path}</div>
            <div class="hub-context">${d.context || '<i>Default sorting</i>'}</div>
            <button class="hub-card-del" title="Remove" onclick="removeDest('${d.path.replace(/\\/g, '\\\\')}')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
        `;
        container.appendChild(card);
    });
}

window.removeDest = async function(path) {
    if(!confirm("Remove destination? AI will need to re-index.")) return;
    await fetch(`${API_URL}/knowledge/destinations?path=${encodeURIComponent(path)}`, {method: 'DELETE'});
    showToast('Removed. Indexing updated.', 'info');
    fetchDestinations();
}

document.getElementById('btn-save-dest').addEventListener('click', async () => {
    const path = document.getElementById('dest-path').value;
    const ctx = document.getElementById('dest-context').value;
    if(!path) return showToast('Path required', 'error');
    
    const res = await fetch(`${API_URL}/knowledge/destinations`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path, context: ctx})
    });
    if(res.ok) {
        showToast('Destination added.', 'success');
        document.getElementById('dest-path').value = '';
        document.getElementById('dest-context').value = '';
        addForm.classList.add('hidden');
        fetchDestinations();
    } else {
        const err = await res.json();
        showToast(err.detail, 'error');
    }
});

// --- History & Corrections ---
async function fetchHistory() {
    const res = await fetch(`${API_URL}/history`);
    const data = await res.json();
    const container = document.getElementById('history-container');
    container.innerHTML = '';
    
    if (data.length === 0) {
        container.innerHTML = '<div style="padding: 2rem; color: var(--text-muted);">No history.</div>';
        return;
    }

    data.forEach(item => {
        const fileName = item.file_path.split('\\').pop().split('/').pop();
        const div = document.createElement('div');
        div.className = 'history-item';
        div.innerHTML = `
            <div class="history-details">
                <span class="history-file">${fileName}</span>
                <span class="history-path">${item.file_path} &rarr; <strong>${item.final_folder}</strong></span>
            </div>
            <button class="secondary-btn" onclick="openCorrection('${item.file_path.replace(/\\/g, '\\\\')}', '${fileName}')">Fix</button>
        `;
        container.appendChild(div);
    });
}

let currentCorrectionFile = "";
const correctionModal = document.getElementById('correction-modal');
window.openCorrection = function(filepath, filename) {
    currentCorrectionFile = filepath;
    document.getElementById('correction-filename').textContent = filename;
    document.getElementById('correction-path').value = '';
    correctionModal.classList.add('active');
}

document.getElementById('btn-submit-correction').addEventListener('click', async () => {
    const newPath = document.getElementById('correction-path').value;
    if(!newPath) return;
    
    const res = await fetch(`${API_URL}/history/correct`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ original_file: currentCorrectionFile, new_folder: newPath })
    });
    if(res.ok) {
        showToast('AI Trained.', 'success');
        correctionModal.classList.remove('active');
        fetchHistory();
    } else {
        const err = await res.json();
        showToast(err.detail, 'error');
    }
});

// --- Settings: Watch Paths ---
async function fetchSettings() {
    const res = await fetch(`${API_URL}/watcher/paths`);
    const data = await res.json();
    const container = document.getElementById('watch-paths-list');
    container.innerHTML = '';
    
    data.forEach(p => {
        const div = document.createElement('div');
        div.className = 'list-item';
        div.innerHTML = `
            <span>${p}</span>
            <button class="hub-card-del" onclick="removeWatchPath('${p.replace(/\\/g, '\\\\')}')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
        `;
        container.appendChild(div);
    });
}

document.getElementById('btn-add-watch-path').addEventListener('click', async () => {
    const path = document.getElementById('watch-path-input').value;
    if(!path) return;
    const res = await fetch(`${API_URL}/watcher/paths`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path})
    });
    if(res.ok) {
        document.getElementById('watch-path-input').value = '';
        fetchSettings();
    } else {
        const err = await res.json();
        showToast(err.detail, 'error');
    }
});

window.removeWatchPath = async function(path) {
    await fetch(`${API_URL}/watcher/paths?path=${encodeURIComponent(path)}`, {method: 'DELETE'});
    fetchSettings();
}

// --- System Reset ---
const resetModal = document.getElementById('reset-modal');
document.getElementById('btn-open-reset-modal').addEventListener('click', () => {
    resetModal.classList.add('active');
});

document.getElementById('btn-submit-reset').addEventListener('click', async () => {
    const confirmText = document.getElementById('reset-confirmation').value;
    if(confirmText !== 'reset') return showToast('Type "reset" to confirm', 'error');
    
    showToast('System wipe in progress...');
    const res = await fetch(`${API_URL}/system/reset`, {method: 'POST'});
    if(res.ok) {
        showToast('System Reset Complete. Closing app.');
        setTimeout(() => window.close(), 2000);
    }
});

// --- Initialization ---
initTheme();
fetchStatus();
setInterval(fetchStatus, 5000);
