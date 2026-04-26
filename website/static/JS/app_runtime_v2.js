/**
 * TimeTable Pro - Main Application Runtime (V2)
 * Handles state management, data fetching, and UI rendering.
 */

const API_BASE = '/api';
let currentState = {
    activeTab: 'dashboard',
    counts: { classrooms: 0, subjects: 0, faculty: 0, student_groups: 0 },
    data: { classrooms: [], subjects: [], faculty: [], student_groups: [] },
    timetables: []
};

// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    switchTab('dashboard');
    updateDashboardStats();
    
    // Auto-update stats every 30 seconds
    setInterval(updateDashboardStats, 30000);
});

// --- Tab Management ---

function switchTab(tabId) {
    currentState.activeTab = tabId;
    
    // Update UI
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.getElementById(`${tabId}-content`).classList.remove('hidden');
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active', 'text-white');
            btn.classList.remove('text-gray-300');
        } else {
            btn.classList.remove('active', 'text-white');
            btn.classList.add('text-gray-300');
        }
    });
    
    // Move indicator
    const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    const indicator = document.getElementById('tabIndicator');
    if (activeBtn && indicator) {
        indicator.style.width = `${activeBtn.offsetWidth}px`;
        indicator.style.left = `${activeBtn.offsetLeft}px`;
    }

    // Tab-specific initializations
    if (tabId === 'dashboard') updateDashboardStats();
}

// --- Dashboard Stats ---

async function updateDashboardStats() {
    try {
        const [cls, sub, fac, std] = await Promise.all([
            fetch(`${API_BASE}/classrooms`).then(r => r.json()),
            fetch(`${API_BASE}/subjects`).then(r => r.json()),
            fetch(`${API_BASE}/faculty`).then(r => r.json()),
            fetch(`${API_BASE}/students`).then(r => r.json())
        ]);
        
        currentState.counts = {
            classrooms: cls.count || cls.length,
            subjects: sub.count || sub.length,
            faculty: fac.count || fac.length,
            student_groups: std.count || std.length
        };
        
        currentState.data = {
            classrooms: cls.classrooms || cls,
            subjects: sub.subjects || sub,
            faculty: fac.faculty || fac,
            student_groups: std.students || std
        };
        
        document.getElementById('classroomCount').textContent = currentState.counts.classrooms;
        document.getElementById('subjectCount').textContent = currentState.counts.subjects;
        document.getElementById('facultyCount').textContent = currentState.counts.faculty;
        document.getElementById('studentGroupCount').textContent = currentState.counts.student_groups;
        
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// --- Quick Actions ---

async function loadSampleData() {
    showLoading(true, 'Loading University Sample Data...');
    try {
        const response = await fetch(`${API_BASE}/load-sample`, { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', 'Sample data loaded successfully!', 'success');
            updateDashboardStats();
        } else {
            showToast('Error', result.message || 'Failed to load sample data', 'error');
        }
    } catch (error) {
        showToast('Error', 'Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

async function generateTimetable() {
    showLoading(true, 'Generating Advanced Timetables...');
    try {
        const response = await fetch(`${API_BASE}/timetable/generate`, { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', 'Conflict-free timetables generated!', 'success');
            switchTab('timetable');
            loadTimetableOptions();
        } else {
            showToast('Generation Failed', result.error || result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Network error occurred during generation', 'error');
    } finally {
        showLoading(false);
    }
}

async function resetAllData() {
    if (!confirm('Are you sure? This will delete ALL university records and generated timetables.')) return;
    
    showLoading(true, 'Wiping Data...');
    try {
        const response = await fetch(`${API_BASE}/reset-data`, { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            showToast('Reset Complete', 'All data has been cleared.', 'success');
            updateDashboardStats();
        }
    } catch (error) {
        showToast('Error', 'Failed to reset data', 'error');
    } finally {
        showLoading(false);
    }
}

// --- Data Entry Management ---

function showDataForm(category) {
    const container = document.getElementById('dataFormContainer');
    
    // Highlight active btn
    document.querySelectorAll('.data-form-btn').forEach(btn => btn.classList.remove('bg-slate-700', 'text-white'));
    event.currentTarget.classList.add('bg-slate-700', 'text-white');
    
    let html = '';
    switch(category) {
        case 'classrooms':
            html = `
                <h3 class="text-2xl font-bold mb-6">Add Classroom</h3>
                <form onsubmit="handleDataSubmit(event, 'classrooms')" class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Room ID</label>
                            <input type="text" name="classroom_id" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Capacity</label>
                            <input type="number" name="capacity" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Room Type</label>
                        <select name="room_type" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                            <option value="Theory">Theory (Lecture Hall)</option>
                            <option value="Practical">Practical (Lab)</option>
                        </select>
                    </div>
                    <button type="submit" class="w-full btn py-3 bg-indigo-500 text-white rounded-lg font-bold">Save Classroom</button>
                </form>
            `;
            break;
        case 'subjects':
            html = `
                <h3 class="text-2xl font-bold mb-6">Add Subject</h3>
                <form onsubmit="handleDataSubmit(event, 'subjects')" class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Subject Code</label>
                            <input type="text" name="subject_code" placeholder="e.g., CSE101" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Subject Name</label>
                            <input type="text" name="subject_name" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                    </div>
                    <div class="grid grid-cols-3 gap-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Branch</label>
                            <input type="text" name="branch" placeholder="CSE" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Semester</label>
                            <input type="number" name="semester" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Credits</label>
                            <input type="number" name="credits" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Type</label>
                            <select name="subject_type" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                                <option value="Theory">Theory</option>
                                <option value="Practical">Practical</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Batch Size (for Practical)</label>
                            <input type="number" name="lab_batch_size" placeholder="30" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                    </div>
                    <button type="submit" class="w-full btn py-3 bg-indigo-500 text-white rounded-lg font-bold">Save Subject</button>
                </form>
            `;
            break;
        case 'faculty':
             html = `
                <h3 class="text-2xl font-bold mb-6">Add Faculty</h3>
                <form onsubmit="handleDataSubmit(event, 'faculty')" class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Faculty ID</label>
                            <input type="text" name="faculty_id" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Full Name</label>
                            <input type="text" name="name" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Subjects (comma separated codes)</label>
                        <input type="text" name="subjects" placeholder="CSE101, CSE102" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Max Hours/Week</label>
                            <input type="number" name="max_hours_per_week" value="18" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Preferred Time</label>
                            <select name="preferred_time" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                                <option value="any">Anytime</option>
                                <option value="morning">Morning Only</option>
                                <option value="afternoon">Afternoon Only</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="w-full btn py-3 bg-indigo-500 text-white rounded-lg font-bold">Save Faculty</button>
                </form>
            `;
            break;
        case 'students':
            html = `
                <h3 class="text-2xl font-bold mb-6">Add Student Group</h3>
                <form onsubmit="handleDataSubmit(event, 'student_groups')" class="space-y-4">
                    <div class="grid grid-cols-3 gap-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Group ID</label>
                            <input type="text" name="group_id" placeholder="CSE_UG_SEM1" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Branch</label>
                            <input type="text" name="branch" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Semester</label>
                            <input type="number" name="semester" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                    </div>
                    <div class="p-4 bg-slate-800 rounded-xl border border-slate-700">
                        <label class="block text-sm font-bold mb-3">Divisions (One per line: Name,Count)</label>
                        <textarea name="divisions_raw" rows="3" placeholder="A,60&#10;B,60" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white font-mono"></textarea>
                    </div>
                    <button type="submit" class="w-full btn py-3 bg-indigo-500 text-white rounded-lg font-bold">Save Student Group</button>
                </form>
            `;
            break;
        case 'timing':
            html = `
                <h3 class="text-2xl font-bold mb-6">Timing Configuration</h3>
                <div class="bg-indigo-500/10 border border-indigo-500/30 rounded-xl p-4 mb-6 text-indigo-300 text-sm">
                    Current system supports standard 9 AM - 4 PM schedule with 50-60 min slots.
                </div>
                <form onsubmit="handleDataSubmit(event, 'timing')" class="space-y-6">
                    <div>
                        <label class="block text-sm text-gray-400 mb-2">Working Days</label>
                        <div class="flex flex-wrap gap-2">
                            ${['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map(d => `
                                <label class="flex items-center space-x-2 bg-slate-700 px-3 py-2 rounded-lg cursor-pointer">
                                    <input type="checkbox" name="working_days" value="${d}" checked>
                                    <span class="text-sm">${d}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Theory Slot (Min)</label>
                            <input type="number" name="theory_duration" value="60" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">Practical Slot (Count)</label>
                            <input type="number" name="practical_slots" value="2" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white">
                        </div>
                    </div>
                    <button type="submit" class="w-full btn py-3 bg-indigo-500 text-white rounded-lg font-bold">Update Configuration</button>
                </form>
            `;
            break;
    }
    container.innerHTML = html;
}

async function handleDataSubmit(event, category) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    
    // Special handling for nested/array data
    if (category === 'faculty' && data.subjects) {
        data.subjects = data.subjects.split(',').map(s => s.trim()).filter(s => s);
    }
    if (category === 'student_groups' && data.divisions_raw) {
        data.divisions = data.divisions_raw.split('\n').map(line => {
            const [name, count] = line.split(',');
            return { division_name: name.trim(), student_count: parseInt(count) || 60 };
        }).filter(d => d.division_name);
        delete data.divisions_raw;
    }
    if (category === 'timing') {
        data.working_days = Array.from(formData.getAll('working_days'));
    }

    showLoading(true, `Saving ${category}...`);
    try {
        const response = await fetch(`${API_BASE}/${category}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Saved', 'Record updated successfully', 'success');
            event.target.reset();
            updateDashboardStats();
        } else {
            showToast('Error', 'Failed to save record', 'error');
        }
    } catch (error) {
        showToast('Error', 'Network error', 'error');
    } finally {
        showLoading(false);
    }
}

// --- Timetable Logic ---

async function loadTimetableOptions() {
    const type = document.getElementById('timetableType').value;
    const entitySelect = document.getElementById('timetableEntity');
    entitySelect.innerHTML = '<option value="">Select Entity</option>';
    
    if (!type) return;
    
    try {
        const response = await fetch(`${API_BASE}/timetable?type=${type}`);
        const data = await response.json();
        const timetables = data.timetables || [];
        
        timetables.forEach(t => {
            let label = t.entity_id;
            if (type === 'student') label = `${t.branch} - Sem ${t.semester} - Div ${t.division}`;
            if (type === 'faculty') label = t.faculty_name || t.entity_id;
            
            const opt = document.createElement('option');
            opt.value = t.entity_id;
            opt.textContent = label;
            entitySelect.appendChild(opt);
        });
    } catch (error) {
        console.error('Error loading options:', error);
    }
}

async function viewSelectedTimetable() {
    const type = document.getElementById('timetableType').value;
    const entity_id = document.getElementById('timetableEntity').value;
    const display = document.getElementById('timetableDisplay');
    
    if (!type || !entity_id) {
        showToast('Selection Required', 'Please select both type and entity', 'warning');
        return;
    }
    
    display.innerHTML = '<div class="py-12 flex justify-center"><div class="spinner"></div></div>';
    
    try {
        // Need to find the timetable_id for the entity_id
        const listResponse = await fetch(`${API_BASE}/timetable?type=${type}`);
        const listData = await listResponse.json();
        const timetableInfo = (listData.timetables || []).find(t => t.entity_id === entity_id);
        
        if (!timetableInfo) {
            display.innerHTML = '<div class="py-12 text-center text-gray-400">Timetable not found</div>';
            return;
        }

        const response = await fetch(`${API_BASE}/timetable/${timetableInfo.timetable_id}`);
        const result = await response.json();
        const timetable = result.timetable || result;
        
        if (timetable) {
            renderTimetable(timetable, display);
            document.getElementById('downloadTimetableBtn').disabled = false;
        } else {
            display.innerHTML = '<div class="py-12 text-center text-gray-400">Timetable not found for this entity</div>';
        }
    } catch (error) {
        display.innerHTML = '<div class="py-12 text-center text-red-400">Error loading timetable data</div>';
    }
}

function renderTimetable(timetable, container) {
    const entries = timetable.entries;
    const days = [...new Set(entries.map(e => e.day))];
    const slots = [...new Set(entries.map(e => e.slot_id))].sort();
    
    // Fetch timing details if available from state
    const timingConfig = {
        S1: "09:00 - 10:00", S2: "10:00 - 11:00", S3: "11:00 - 11:15",
        S4: "11:15 - 12:15", S5: "12:15 - 13:15", S6: "13:15 - 14:00",
        S7: "14:00 - 15:00", S8: "15:00 - 16:00"
    };

    let html = `
        <div id="timetableExportArea" class="timetable-export-card">
            <div class="mb-8 text-center">
                <h1 class="text-4xl font-extrabold tracking-tight text-white mb-2">
                    ${timetable.entity_type === 'student' ? 'CLASS SCHEDULE' : (timetable.entity_type === 'faculty' ? 'FACULTY SCHEDULE' : 'ROOM SCHEDULE')}
                </h1>
                <div class="flex justify-center items-center space-x-3 text-indigo-300 font-medium">
                    <span class="bg-indigo-500/20 px-3 py-1 rounded-full border border-indigo-500/30">
                        ${timetable.entity_id}
                    </span>
                    ${timetable.branch ? `<span class="opacity-40">•</span><span>${timetable.branch}</span>` : ''}
                    ${timetable.semester ? `<span class="opacity-40">•</span><span>Semester ${timetable.semester}</span>` : ''}
                </div>
            </div>

            <div class="timetable-grid">
                <div class="timetable-time-cell !bg-transparent !p-0"></div>
                ${days.map(day => `<div class="timetable-header">${day}</div>`).join('')}
                
                ${slots.map(slotId => {
                    const timeRange = timingConfig[slotId] || slotId;
                    const [start, end] = timeRange.split(' - ');
                    
                    let slotHtml = `
                        <div class="timetable-time-cell">
                            <span class="text-white font-bold">${start}</span>
                            <span class="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">${end}</span>
                            <span class="text-[9px] text-indigo-400 font-mono mt-1 opacity-60">${slotId}</span>
                        </div>
                    `;
                    
                    days.forEach(day => {
                        const entry = entries.find(e => e.day === day && e.slot_id === slotId);
                        if (!entry) {
                            slotHtml += `<div class="timetable-cell free"></div>`;
                        } else if (entry.entry_type === 'break') {
                            slotHtml += `
                                <div class="timetable-cell break">
                                    <span class="text-[10px] uppercase tracking-widest text-gray-500 font-bold text-center">Break</span>
                                </div>
                            `;
                        } else if (entry.entry_type === 'empty' || entry.entry_type === 'free') {
                            slotHtml += `<div class="timetable-cell free"></div>`;
                        } else {
                            const isPractical = entry.entry_type === 'practical';
                            slotHtml += `
                                <div class="timetable-cell ${isPractical ? 'practical' : 'theory'} group">
                                    <div class="timetable-cell-title text-white mb-1">${entry.subject_code}</div>
                                    <div class="timetable-cell-subtitle text-white/80 font-medium truncate mb-1.5">${entry.subject_name}</div>
                                    <div class="flex flex-col space-y-1 mt-auto">
                                        <div class="timetable-cell-meta flex items-center text-white/60">
                                            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                                            <span class="truncate">${entry.faculty_name || entry.faculty_id}</span>
                                        </div>
                                        <div class="timetable-cell-meta flex items-center text-white/60">
                                            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                                            <span>${entry.classroom_id}</span>
                                        </div>
                                        ${entry.batch ? `
                                            <div class="mt-1 px-1.5 py-0.5 bg-black/30 rounded text-[9px] font-bold text-white/90 w-fit uppercase">
                                                Batch: ${entry.batch}
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            `;
                        }
                    });
                    return slotHtml;
                }).join('')}
            </div>
            
            <div class="mt-12 flex justify-between items-center text-[10px] text-gray-600 border-t border-white/5 pt-6">
                <div class="flex items-center space-x-4">
                    <div class="flex items-center"><div class="w-2 h-2 rounded-full bg-blue-500 mr-2"></div> Theory</div>
                    <div class="flex items-center"><div class="w-2 h-2 rounded-full bg-green-500 mr-2"></div> Practical</div>
                </div>
                <div class="font-mono">GENERATED BY TIMETABLE PRO SYSTEM • ${new Date().toLocaleDateString()}</div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// --- Utilities ---

function showLoading(show, text = 'Processing...') {
    const overlay = document.getElementById('loadingOverlay');
    const textEl = document.getElementById('loadingText');
    if (show) {
        textEl.textContent = text;
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

function showToast(title, message, type = 'success') {
    const toast = document.getElementById('toast');
    const titleEl = document.getElementById('toastMessage');
    const icon = document.getElementById('toastIcon');
    
    titleEl.innerHTML = `<span class="font-bold">${title}:</span> ${message}`;
    
    // Color mapping
    const colors = {
        success: 'text-green-400',
        error: 'text-red-400',
        warning: 'text-yellow-400'
    };
    
    toast.querySelector('#toastContent').className = `glass rounded-xl px-6 py-4 flex items-center space-x-3 shadow-2xl border-l-4 ${type === 'success' ? 'border-green-500' : (type === 'error' ? 'border-red-500' : 'border-yellow-500')}`;
    
    toast.classList.remove('translate-y-32');
    setTimeout(() => {
        toast.classList.add('translate-y-32');
    }, 4000);
}

function viewDataModal(category) {
    const modal = document.getElementById('dataModal');
    const title = document.getElementById('modalTitle');
    const content = document.getElementById('modalContent');
    
    title.textContent = `${category.charAt(0).toUpperCase() + category.slice(1)} Records`;
    modal.classList.remove('hidden');
    
    const records = currentState.data[category] || [];
    
    if (records.length === 0) {
        content.innerHTML = '<p class="text-gray-400 text-center py-8">No records found. Load sample data or add manual entries.</p>';
        return;
    }
    
    let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">';
    records.forEach(item => {
        const id = item.classroom_id || item.subject_code || item.faculty_id || item.group_id;
        html += `
            <div class="bg-slate-800 p-4 rounded-xl border border-slate-700 relative group">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-xs font-bold text-indigo-400 font-mono">${id}</span>
                    <button onclick="deleteRecord('${category}', '${id}')" class="text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
                <div class="text-white font-bold mb-1">${item.name || item.subject_name || item.branch || 'Record'}</div>
                <div class="text-[10px] text-gray-500 flex flex-wrap gap-1">
                    ${Object.entries(item).filter(([k]) => !['_id', 'name', 'subject_name'].includes(k)).map(([k, v]) => `
                        <span class="bg-slate-700 px-1.5 py-0.5 rounded">${k}: ${Array.isArray(v) ? v.length : v}</span>
                    `).join('')}
                </div>
            </div>
        `;
    });
    html += '</div>';
    content.innerHTML = html;
}

async function deleteRecord(category, id) {
    if (!confirm(`Delete ${id}?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/${category}/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showToast('Deleted', 'Record removed', 'success');
            updateDashboardStats();
            viewDataModal(category); // Refresh modal
        }
    } catch (error) {
        showToast('Error', 'Failed to delete', 'error');
    }
}

function closeDataModal() {
    document.getElementById('dataModal').classList.add('hidden');
}

async function downloadTimetableAsImage() {
    const element = document.getElementById('timetableExportArea');
    if (!element) return;
    
    showLoading(true, 'Preparing High-Res Image...');
    try {
        const canvas = await html2canvas(element, {
            backgroundColor: '#0f172a',
            scale: 2,
            logging: false,
            useCORS: true
        });
        
        const link = document.createElement('a');
        link.download = `timetable_${new Date().getTime()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
        showToast('Exported', 'Timetable image downloaded', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showToast('Export Error', 'Failed to generate image', 'error');
    } finally {
        showLoading(false);
    }
}
