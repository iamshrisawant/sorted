const API_URL = "http://127.0.0.1:8099/api";
let onboardingShown = false;

// --- Helper: Native Folder Picker ---
async function pickFolderNative(inputId) {
    if (window.pywebview && window.pywebview.api) {
        try {
            const path = await window.pywebview.api.pick_folder();
            if (path) {
                const input = document.getElementById(inputId);
                if (input) {
                    input.value = path;
                    // Trigger any change listeners
                    input.dispatchEvent(new Event('input'));
                }
            }
        } catch (e) {
            console.error("Picker failed", e);
            showToast("Failed to open folder picker.", "error");
        }
    } else {
        showToast("Native picker unavailable. Are you running in a browser?", "error");
    }
}

// --- Main UI Logic ---
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNavigation();
    initServiceControls();
    initPickers();
    initModals();
    
    // Initial fetch
    fetchStatus();
    // Start status polling
    setInterval(fetchStatus, 5000);
});

function initNavigation() {
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
}

function refreshView(viewId) {
    if(viewId === 'destinations') fetchDestinations();
    if(viewId === 'history') fetchHistory();
    if(viewId === 'settings') fetchSettings();
    if(viewId === 'dashboard') fetchStatus();
}

function initPickers() {
    // Mapping of button IDs to their respective input IDs
    const pickerMap = {
        'btn-pick-ob-watch': 'ob-watch-path',
        'btn-pick-dest-path': 'dest-path',
        'btn-pick-watch-path': 'watch-path-input',
        'btn-pick-sort-path': 'sort-target-path',
        'btn-pick-correction-path': 'correction-path'
    };

    Object.entries(pickerMap).forEach(([btnId, inputId]) => {
        const btn = document.getElementById(btnId);
        const input = document.getElementById(inputId);
        if (btn) btn.addEventListener('click', (e) => {
            e.preventDefault();
            pickFolderNative(inputId);
        });
        // Also allow clicking the readonly input itself to browse
        if (input) input.addEventListener('click', () => pickFolderNative(inputId));
    });
}

function initServiceControls() {
    const startBtn = document.getElementById('btn-start-watcher');
    const stopBtn = document.getElementById('btn-stop-watcher');
    const restartBtn = document.getElementById('btn-restart-watcher');
    const regBtn = document.getElementById('btn-register');
    const unregBtn = document.getElementById('btn-unregister');

    if (startBtn) startBtn.addEventListener('click', async () => {
        const res = await fetch(`${API_URL}/watcher/control?action=start`, {method: 'POST'});
        const data = await res.json();
        showToast(data.success ? 'Watcher started.' : 'Startup failed.', data.success ? 'success' : 'error');
        setTimeout(fetchStatus, 1500);
    });

    if (stopBtn) stopBtn.addEventListener('click', async () => {
        const res = await fetch(`${API_URL}/watcher/control?action=stop`, {method: 'POST'});
        showToast('Watcher stopped.', 'info');
        setTimeout(fetchStatus, 1500);
    });

    if (restartBtn) restartBtn.addEventListener('click', async () => {
        showToast('Restarting watcher...');
        const res = await fetch(`${API_URL}/watcher/control?action=restart`, {method: 'POST'});
        showToast('Watcher restarted.', 'success');
        setTimeout(fetchStatus, 1500);
    });

    if (regBtn) regBtn.addEventListener('click', async () => {
        await fetch(`${API_URL}/watcher/control?action=register`, {method: 'POST'});
        showToast('Registered for Startup', 'success');
        fetchStatus();
    });

    if (unregBtn) unregBtn.addEventListener('click', async () => {
        await fetch(`${API_URL}/watcher/control?action=unregister`, {method: 'POST'});
        showToast('Removed from Startup', 'info');
        fetchStatus();
    });
}

function initModals() {
    // Sort Modal
    const sortModal = document.getElementById('sort-modal');
    const openSortBtn = document.getElementById('btn-open-sort-modal');
    if (openSortBtn) openSortBtn.addEventListener('click', () => {
        document.getElementById('sort-target-path').value = '';
        sortModal.classList.add('active');
    });

    document.getElementById('btn-submit-sort').addEventListener('click', async () => {
        const path = document.getElementById('sort-target-path').value;
        sortModal.classList.remove('active');
        showToast('Manual Deep Scan started...', 'info');
        await fetch(`${API_URL}/sort/manual`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({target_folder: path || null})
        });
        fetchStatus();
    });

    // Reset Modal
    document.getElementById('btn-open-reset-modal').addEventListener('click', () => {
        document.getElementById('reset-confirmation').value = '';
        document.getElementById('reset-modal').classList.add('active');
    });

    document.getElementById('btn-submit-reset').addEventListener('click', async () => {
        const confirmText = document.getElementById('reset-confirmation').value;
        if(confirmText !== 'reset') return showToast('Type "reset" to confirm', 'error');
        document.getElementById('reset-modal').classList.remove('active');
        showToast('System wipe in progress...');
        const res = await fetch(`${API_URL}/system/reset`, {method: 'POST'});
        if(res.ok) {
            showToast('System Reset Complete. Closing app.');
            setTimeout(() => window.close(), 2000);
        }
    });

    // Onboarding Submit
    const obSubmitBtn = document.getElementById('btn-submit-onboarding');
    if (obSubmitBtn) {
        obSubmitBtn.addEventListener('click', async () => {
            const path = document.getElementById('ob-watch-path').value;
            if (!path) return showToast('Please select a folder to start.', 'error');
            
            const res = await fetch(`${API_URL}/watcher/paths`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path})
            });
            
            if (res.ok) {
                document.getElementById('onboarding-modal').classList.remove('active');
                showToast('Setup complete!', 'success');
                document.querySelector('.nav-item[data-target="destinations"]').click();
            }
        });
    }
}

// --- API Interactions ---

async function fetchStatus() {
    try {
        const res = await fetch(`${API_URL}/status`);
        if (!res.ok) return;
        const data = await res.json();
        
        // Update Sidebar
        const indicator = document.querySelector('.status-indicator');
        const title = document.querySelector('.status-title');
        const sub = document.querySelector('.status-sub');
        
        if (data.online) {
            indicator.classList.add('online');
            title.textContent = 'System Online';
            sub.textContent = 'Watcher active';
            document.getElementById('stat-state').textContent = 'Active';
            document.getElementById('stat-state').style.color = 'var(--success)';
        } else {
            indicator.classList.remove('online');
            title.textContent = 'System Offline';
            sub.textContent = 'Watcher stopped';
            document.getElementById('stat-state').textContent = 'Stopped';
            document.getElementById('stat-state').style.color = 'var(--danger)';
        }

        // Update Dashboard Stats
        document.getElementById('stat-state-meta').textContent = data.registered ? 'Auto-startup enabled' : 'Manual startup only';
        document.getElementById('stat-hubs').textContent = data.total_destinations;
        
        // Update Banner
        const banner = document.getElementById('indexing-banner');
        if (data.builder_busy) banner.classList.remove('hidden');
        else banner.classList.add('hidden');

        // Update Queue
        const queueSection = document.getElementById('active-queue-section');
        const queueList = document.getElementById('active-queue-list');
        if (data.processing_queue && data.processing_queue.length > 0) {
            queueSection.classList.remove('hidden');
            queueList.innerHTML = '';
            data.processing_queue.forEach(path => {
                const fileName = path.split(/\\|\//).pop();
                const item = document.createElement('div');
                item.className = 'queue-item';
                item.textContent = `Processing: ${fileName}`;
                queueList.appendChild(item);
            });
        } else {
            queueSection.classList.add('hidden');
        }

        // Check Review Queue
        fetchReviewQueue();
        fetchWaitQueue();

        // Onboarding
        if (!onboardingShown && data.watch_paths.length === 0 && data.total_destinations === 0) {
            document.getElementById('onboarding-modal').classList.add('active');
            onboardingShown = true;
        }
    } catch (e) { console.error("Status check failed", e); }
}

// --- Destinations ---
const addForm = document.getElementById('dest-add-form');
const addBtn = document.getElementById('btn-add-dest');
const cancelBtn = document.getElementById('btn-cancel-dest');

if (addBtn) addBtn.addEventListener('click', () => addForm.classList.remove('hidden'));
if (cancelBtn) cancelBtn.addEventListener('click', () => addForm.classList.add('hidden'));

async function fetchDestinations() {
    const res = await fetch(`${API_URL}/knowledge/destinations`);
    const data = await res.json();
    const container = document.getElementById('destinations-list');
    container.innerHTML = '';
    
    // Update dashboard hub count immediately if visible
    const dashHubs = document.getElementById('stat-hubs');
    if (dashHubs) dashHubs.textContent = data.length;

    if(data.length === 0) {
        container.innerHTML = '<p class="text-muted" style="padding: 1rem;">No knowledge hubs configured.</p>';
        return;
    }
    
    data.forEach(d => {
        const card = document.createElement('div');
        card.className = 'hub-card panel';
        card.innerHTML = `
            <div class="hub-header">
                <div class="hub-path">${d.path}</div>
                <button class="icon-btn-del" title="Remove Destination" onclick="removeDest('${d.path.replace(/\\/g, '\\\\')}')">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </div>
            <div class="hub-context">${d.context || '<i>Automatic semantic extraction enabled.</i>'}</div>
        `;
        container.appendChild(card);
    });
}

window.removeDest = async function(path) {
    if(!confirm("Remove this destination? The AI will forget how to sort files here.")) return;
    await fetch(`${API_URL}/knowledge/destinations?path=${encodeURIComponent(path)}`, {method: 'DELETE'});
    showToast('Destination removed.', 'info');
    fetchDestinations();
}

document.getElementById('btn-save-dest').addEventListener('click', async () => {
    const path = document.getElementById('dest-path').value;
    const ctx = document.getElementById('dest-context').value;
    if(!path) return showToast('Please select a folder path.', 'error');
    
    try {
        const res = await fetch(`${API_URL}/knowledge/destinations`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path, context: ctx})
        });
        
        if(res.ok) {
            showToast('Destination added. Indexing started...', 'success');
            document.getElementById('dest-path').value = '';
            document.getElementById('dest-context').value = '';
            addForm.classList.add('hidden');
            fetchDestinations();
        } else {
            const err = await res.json();
            showToast(err.detail || 'Failed to add destination', 'error');
        }
    } catch (e) {
        showToast('Connection error', 'error');
    }
});

// --- History & Review Glue ---

async function fetchHistory() {
    const res = await fetch(`${API_URL}/history`);
    const data = await res.json();
    const container = document.getElementById('history-container');
    container.innerHTML = '';
    
    if (data.length === 0) {
        container.innerHTML = '<div style="padding: 2rem; color: var(--text-muted);">No sorting history available.</div>';
        return;
    }

    data.forEach(item => {
        const fileName = item.file_path.split(/\\|\//).pop();
        const div = document.createElement('div');
        div.className = 'history-item';
        div.innerHTML = `
            <div class="history-details">
                <span class="history-file">${fileName}</span>
                <span class="history-path">${item.file_path} &rarr; <strong>${item.final_folder.split(/\\|\//).pop()}</strong></span>
            </div>
            <div class="history-actions">
                <button class="secondary-btn btn-sm" onclick="openCorrection('${item.file_path.replace(/\\/g, '\\\\')}', '${fileName}')">Fix Error</button>
                <button class="icon-btn-del" title="Delete Log Entry" onclick="deleteHistoryItem('${item.file_path.replace(/\\/g, '\\\\')}')">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </div>
        `;
        container.appendChild(div);
    });
}

window.deleteHistoryItem = async function(path) {
    if(!confirm("Remove this entry from history?")) return;
    await fetch(`${API_URL}/history?path=${encodeURIComponent(path)}`, {method: 'DELETE'});
    showToast('Entry removed.', 'info');
    fetchHistory();
}

let currentCorrectionFile = "";
window.openCorrection = function(filepath, filename) {
    currentCorrectionFile = filepath;
    document.getElementById('correction-filename').textContent = filename;
    document.getElementById('correction-path').value = '';
    document.getElementById('correction-modal').classList.add('active');
}

document.getElementById('btn-submit-correction').addEventListener('click', async () => {
    const newPath = document.getElementById('correction-path').value;
    if(!newPath) return showToast('Please select a folder.', 'error');
    
    const res = await fetch(`${API_URL}/history/correct`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ original_file: currentCorrectionFile, new_folder: newPath })
    });
    if(res.ok) {
        showToast('Mistake corrected. AI is learning.', 'success');
        document.getElementById('correction-modal').classList.remove('active');
        fetchHistory();
    }
});

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
            <button class="icon-btn-del" onclick="removeWatchPath('${p.replace(/\\/g, '\\\\')}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
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
    }
});

window.removeWatchPath = async function(path) {
    await fetch(`${API_URL}/watcher/paths?path=${encodeURIComponent(path)}`, {method: 'DELETE'});
    fetchSettings();
}

// --- Theme Refined ---
function initTheme() {
    const themeBtns = document.querySelectorAll('.theme-btn');
    const storedTheme = localStorage.getItem('sortedpc-theme') || 'system';
    document.documentElement.setAttribute('data-theme', storedTheme);

    themeBtns.forEach(btn => {
        if (btn.getAttribute('data-theme-val') === storedTheme) btn.classList.add('active');
        btn.addEventListener('click', () => {
            themeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const val = btn.getAttribute('data-theme-val');
            document.documentElement.setAttribute('data-theme', val);
            localStorage.setItem('sortedpc-theme', val);
        });
    });
}

// --- Status/Toasts Boilerplate ---
function showToast(message, type="info") {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

async function fetchReviewQueue() {
    try {
        const res = await fetch(`${API_URL}/review/queue`);
        const data = await res.json();
        const section = document.getElementById('review-queue-section');
        const container = document.getElementById('review-queue-list');
        if (data.length === 0) { section.classList.add('hidden'); return; }
        section.classList.remove('hidden');
        container.innerHTML = '';
        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'review-card';
            let suggestionHtml = '';
            if (item.suggestions?.length > 0) {
                suggestionHtml = `<div class="review-suggestions">
                    ${item.suggestions.map(s => `<span class="suggestion-tag" onclick="applyReview('${item.file_path.replace(/\\/g, '\\\\')}', '${s.replace(/\\/g, '\\\\')}')">${s.split(/\\|\//).pop()}</span>`).join('')}
                </div>`;
            }
            card.innerHTML = `
                <div class="review-main">
                    <div class="review-info">
                        <div class="review-file">${item.file_name}</div>
                        <div class="review-reason">${item.reason}</div>
                    </div>
                    <div class="review-actions">
                        <button class="secondary-btn btn-sm" onclick="openCorrection('${item.file_path.replace(/\\/g, '\\\\')}', '${item.file_name}')">Assign</button>
                        <button class="icon-btn-del" onclick="ignoreReview('${item.file_path.replace(/\\/g, '\\\\')}')">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        </button>
                    </div>
                </div>
                ${suggestionHtml}`;
            container.appendChild(card);
        });
    } catch (e) { console.error(e); }
}

window.applyReview = async function(filePath, targetFolder) {
    const res = await fetch(`${API_URL}/review/apply`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ file_path: filePath, target_folder: targetFolder })
    });
    if (res.ok) { fetchReviewQueue(); showToast("File Sorted", "success"); }
}

window.ignoreReview = async function(filePath) {
    await fetch(`${API_URL}/review/ignore?file_path=${encodeURIComponent(filePath)}`, {method: 'DELETE'});
    fetchReviewQueue();
}

async function fetchWaitQueue() {
    try {
        const res = await fetch(`${API_URL}/waitlist`);
        const data = await res.json();
        
        const section = document.getElementById('wait-queue-section');
        const list = document.getElementById('wait-queue-list');
        const countStat = document.getElementById('stat-waiting');

        if (countStat) countStat.textContent = data.length;

        if (!data || data.length === 0) {
            section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');
        list.innerHTML = '';
        data.forEach(item => {
            const row = document.createElement('div');
            row.className = 'queue-item';
            row.style.borderLeft = '3px solid var(--primary)';
            row.textContent = `Pending Hub indexing: ${item.file_name}`;
            list.appendChild(row);
        });
    } catch (e) { console.error(e); }
}
