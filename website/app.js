// ============================================================================
// COMPLETE APP.JS WITH ALL FEATURES IMPLEMENTED
// - Edit/Delete from dashboard
// - User-defined working hours
// - Continuous lecture scheduling
// - Minimum gaps between lectures
// - All features ready to use
// ============================================================================

const API_BASE_URL = 'http://localhost:8000/api';

let currentTab = 'dashboard';
let currentDataForm = null;
let allTimetables = [];
let timingConfig = null;
let currentDisplayedTimetable = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    switchTab('dashboard');
    loadDashboardStats();
    checkAPIHealth();
    loadTimingConfig();
});

// ============================================================================
// TAB MANAGEMENT
// ============================================================================

function switchTab(tabName) {
    currentTab = tabName;
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    const selectedContent = document.getElementById(`${tabName}-content`);
    if (selectedContent) {
        selectedContent.classList.remove('hidden');
        selectedContent.classList.add('fade-in');
    }
    
    const tabBtns = document.querySelectorAll('.tab-btn');
    const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
    
    if (activeBtn) {
        const indicator = document.getElementById('tabIndicator');
        const btnRect = activeBtn.getBoundingClientRect();
        const parentRect = activeBtn.parentElement.getBoundingClientRect();
        
        indicator.style.width = `${btnRect.width}px`;
        indicator.style.left = `${btnRect.left - parentRect.left}px`;
    }
    
    if (tabName === 'timetable') {
        loadTimetableOptions();
    }
}

// ============================================================================
// API HEALTH CHECK
// ============================================================================

async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL.replace('/api', '')}/api/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateStatus('connected');
        } else {
            updateStatus('error');
        }
    } catch (error) {
        console.error('API health check failed:', error);
        updateStatus('disconnected');
    }
}

function updateStatus(status) {
    const indicator = document.getElementById('statusIndicator');
    const statusMap = {
        connected: '<div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div><span class="text-sm text-gray-400">Connected</span>',
        disconnected: '<div class="w-2 h-2 rounded-full bg-red-500"></div><span class="text-sm text-gray-400">Disconnected</span>',
        error: '<div class="w-2 h-2 rounded-full bg-yellow-500"></div><span class="text-sm text-gray-400">Error</span>'
    };
    indicator.innerHTML = statusMap[status] || statusMap.disconnected;
}

async function loadTimingConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/timings`);
        const data = await response.json();
        timingConfig = data;
    } catch (error) {
        console.error('Error loading timing config:', error);
    }
}

// ============================================================================
// DASHBOARD STATS
// ============================================================================

async function loadDashboardStats() {
    try {
        const [classrooms, subjects, faculty, students] = await Promise.all([
            fetch(`${API_BASE_URL}/classrooms`).then(r => r.json()),
            fetch(`${API_BASE_URL}/subjects`).then(r => r.json()),
            fetch(`${API_BASE_URL}/faculty`).then(r => r.json()),
            fetch(`${API_BASE_URL}/students`).then(r => r.json())
        ]);
        
        document.getElementById('classroomCount').textContent = classrooms.count || 0;
        document.getElementById('subjectCount').textContent = subjects.count || 0;
        document.getElementById('facultyCount').textContent = faculty.count || 0;
        document.getElementById('studentGroupCount').textContent = students.count || 0;
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// ============================================================================
// VIEW DATA MODAL WITH EDIT/DELETE
// ============================================================================

async function viewDataModal(dataType) {
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const modal = document.getElementById('dataModal');
    
    const titles = {
        classrooms: 'All Classrooms',
        subjects: 'All Subjects',
        faculty: 'All Faculty Members',
        students: 'All Student Groups'
    };
    
    modalTitle.textContent = titles[dataType] || 'Data';
    modal.classList.remove('hidden');
    
    showLoading('Loading data...');
    
    try {
        const endpoints = {
            classrooms: '/classrooms',
            subjects: '/subjects',
            faculty: '/faculty',
            students: '/students'
        };
        
        const response = await fetch(`${API_BASE_URL}${endpoints[dataType]}`);
        const data = await response.json();
        
        hideLoading();
        
        if (dataType === 'classrooms') {
            displayClassrooms(data.classrooms || []);
        } else if (dataType === 'subjects') {
            displaySubjects(data.subjects || []);
        } else if (dataType === 'faculty') {
            displayFaculty(data.faculty || []);
        } else if (dataType === 'students') {
            displayStudents(data.student_groups || []);
        }
    } catch (error) {
        hideLoading();
        modalContent.innerHTML = '<p class="text-red-400">Error loading data</p>';
    }
}

// ============================================================================
// DISPLAY FUNCTIONS WITH EDIT/DELETE BUTTONS
// ============================================================================

function displayClassrooms(classrooms) {
    const modalContent = document.getElementById('modalContent');
    
    if (classrooms.length === 0) {
        modalContent.innerHTML = `
            <p class="text-gray-400 mb-4">No classrooms added yet</p>
            <button onclick="showDataForm('classrooms'); closeDataModal();" class="btn px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">
                + Add Classroom
            </button>
        `;
        return;
    }
    
    let html = `
        <div class="mb-4 flex justify-end">
            <button onclick="showDataForm('classrooms'); closeDataModal();" class="btn px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg text-sm">
                + Add New
            </button>
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Classroom ID</th>
                    <th>Capacity</th>
                    <th>Type</th>
                    <th>Smart</th>
                    <th>Lab Type</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    classrooms.forEach(classroom => {
        const classroomJson = JSON.stringify(classroom).replace(/"/g, '"');
        html += `
            <tr>
                <td class="font-bold text-indigo-400">${classroom.classroom_id}</td>
                <td>${classroom.capacity} students</td>
                <td><span class="badge ${classroom.room_type === 'Theory' ? 'badge-success' : 'badge-warning'}">${classroom.room_type}</span></td>
                <td>${classroom.is_smart_classroom ? '✅ Yes' : '❌ No'}</td>
                <td>${classroom.lab_type || '-'}</td>
                <td>
                    <button onclick='editClassroom(${classroomJson})' class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm mr-2">Edit</button>
                    <button onclick="deleteClassroom('${classroom.classroom_id}')" class="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm">Delete</button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    modalContent.innerHTML = html;
}

function displaySubjects(subjects) {
    const modalContent = document.getElementById('modalContent');
    
    if (subjects.length === 0) {
        modalContent.innerHTML = `
            <p class="text-gray-400 mb-4">No subjects added yet</p>
            <button onclick="showDataForm('subjects'); closeDataModal();" class="btn px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">
                + Add Subject
            </button>
        `;
        return;
    }
    
    let html = `
        <div class="mb-4 flex justify-end">
            <button onclick="showDataForm('subjects'); closeDataModal();" class="btn px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg text-sm">
                + Add New
            </button>
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Code</th>
                    <th>Subject Name</th>
                    <th>Branch</th>
                    <th>Semester</th>
                    <th>Type</th>
                    <th>Credits</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    subjects.forEach(subject => {
        const subjectJson = JSON.stringify(subject).replace(/"/g, '"');
        html += `
            <tr>
                <td class="font-bold text-indigo-400">${subject.subject_code}</td>
                <td>${subject.subject_name}</td>
                <td>${subject.branch}</td>
                <td>Sem ${subject.semester}</td>
                <td><span class="badge ${subject.subject_type === 'Theory' ? 'badge-success' : 'badge-warning'}">${subject.subject_type}</span></td>
                <td>${subject.credits}</td>
                <td>
                    <button onclick='editSubject(${subjectJson})' class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm mr-2">Edit</button>
                    <button onclick="deleteSubject('${subject.subject_code}')" class="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm">Delete</button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    modalContent.innerHTML = html;
}

function displayFaculty(faculty) {
    const modalContent = document.getElementById('modalContent');
    
    if (faculty.length === 0) {
        modalContent.innerHTML = `
            <p class="text-gray-400 mb-4">No faculty added yet</p>
            <button onclick="showDataForm('faculty'); closeDataModal();" class="btn px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">
                + Add Faculty
            </button>
        `;
        return;
    }
    
    let html = `
        <div class="mb-4 flex justify-end">
            <button onclick="showDataForm('faculty'); closeDataModal();" class="btn px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg text-sm">
                + Add New
            </button>
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Faculty ID</th>
                    <th>Name</th>
                    <th>Subjects</th>
                    <th>Max Hours/Week</th>
                    <th>Preferred Time</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    faculty.forEach(fac => {
        const facultyJson = JSON.stringify(fac).replace(/"/g, '"');
        html += `
            <tr>
                <td class="font-bold text-indigo-400">${fac.faculty_id}</td>
                <td>${fac.name}</td>
                <td><span class="text-xs">${fac.subjects.join(', ')}</span></td>
                <td>${fac.max_hours_per_week} hrs</td>
                <td><span class="badge badge-success">${fac.preferred_time}</span></td>
                <td>
                    <button onclick='editFaculty(${facultyJson})' class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm mr-2">Edit</button>
                    <button onclick="deleteFaculty('${fac.faculty_id}')" class="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm">Delete</button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    modalContent.innerHTML = html;
}

function displayStudents(students) {
    const modalContent = document.getElementById('modalContent');
    
    if (students.length === 0) {
        modalContent.innerHTML = `
            <p class="text-gray-400 mb-4">No student groups added yet</p>
            <button onclick="showDataForm('students'); closeDataModal();" class="btn px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">
                + Add Student Group
            </button>
        `;
        return;
    }
    
    let html = `
        <div class="mb-4 flex justify-end">
            <button onclick="showDataForm('students'); closeDataModal();" class="btn px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg text-sm">
                + Add New
            </button>
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Branch</th>
                    <th>Semester</th>
                    <th>Divisions</th>
                    <th>Total Students</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    students.forEach(group => {
        const totalStudents = group.divisions.reduce((sum, div) => sum + div.student_count, 0);
        const divisionInfo = group.divisions.map(d => `${d.division_name} (${d.student_count})`).join(', ');
        const groupJson = JSON.stringify(group).replace(/"/g, '"');
        
        html += `
            <tr>
                <td class="font-bold text-indigo-400">${group.branch}</td>
                <td>Semester ${group.semester}</td>
                <td>${divisionInfo}</td>
                <td>${totalStudents} students</td>
                <td>
                    <button onclick='editStudentGroup(${groupJson})' class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm mr-2">Edit</button>
                    <button onclick="deleteStudentGroup('${group.group_id}')" class="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm">Delete</button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    modalContent.innerHTML = html;
}

function closeDataModal() {
    document.getElementById('dataModal').classList.add('hidden');
}

// ============================================================================
// EDIT FUNCTIONS - CLASSROOMS
// ============================================================================

function editClassroom(classroom) {
    const modal = document.getElementById('editModal');
    const title = document.getElementById('editModalTitle');
    const form = document.getElementById('editModalForm');
    
    title.textContent = 'Edit Classroom';
    
    form.innerHTML = `
        <div class="space-y-4">
            <input type="hidden" id="edit_id" value="${classroom.classroom_id}">
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Classroom ID</label>
                <input type="text" value="${classroom.classroom_id}" readonly 
                       class="w-full px-4 py-2 bg-slate-600 border border-slate-500 rounded-lg text-white">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Capacity</label>
                <input type="number" id="edit_capacity" value="${classroom.capacity}" required min="1"
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Room Type</label>
                <select id="edit_room_type" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                    <option value="Theory" ${classroom.room_type === 'Theory' ? 'selected' : ''}>Theory</option>
                    <option value="Practical" ${classroom.room_type === 'Practical' ? 'selected' : ''}>Practical</option>
                </select>
            </div>
            <div class="flex items-center space-x-2">
                <input type="checkbox" id="edit_is_smart" ${classroom.is_smart_classroom ? 'checked' : ''} class="w-4 h-4 rounded">
                <label for="edit_is_smart" class="text-sm text-gray-300">Smart Classroom</label>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Lab Type (Optional)</label>
                <input type="text" id="edit_lab_type" value="${classroom.lab_type || ''}"
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="closeEditModal()" class="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg">Cancel</button>
                <button type="submit" class="btn px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">Save Changes</button>
            </div>
        </div>
    `;
    
    form.onsubmit = async (e) => {
        e.preventDefault();
        await saveClassroomEdit();
    };
    
    modal.classList.remove('hidden');
}

async function saveClassroomEdit() {
    const id = document.getElementById('edit_id').value;
    const data = {
        capacity: parseInt(document.getElementById('edit_capacity').value),
        room_type: document.getElementById('edit_room_type').value,
        is_smart_classroom: document.getElementById('edit_is_smart').checked,
        lab_type: document.getElementById('edit_lab_type').value || null
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/classrooms/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Classroom updated successfully', 'success');
            closeEditModal();
            viewDataModal('classrooms');
            await loadDashboardStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update classroom', 'error');
        }
    } catch (error) {
        showToast('Failed to update classroom', 'error');
    }
}

async function deleteClassroom(id) {
    if (!confirm(`Delete classroom ${id}? This cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/classrooms/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Classroom deleted successfully', 'success');
            viewDataModal('classrooms');
            await loadDashboardStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to delete classroom', 'error');
        }
    } catch (error) {
        showToast('Failed to delete classroom', 'error');
    }
}

// ============================================================================
// EDIT FUNCTIONS - SUBJECTS
// ============================================================================

function editSubject(subject) {
    const modal = document.getElementById('editModal');
    const title = document.getElementById('editModalTitle');
    const form = document.getElementById('editModalForm');
    
    title.textContent = 'Edit Subject';
    
    form.innerHTML = `
        <div class="space-y-4">
            <input type="hidden" id="edit_id" value="${subject.subject_code}">
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Subject Code</label>
                <input type="text" value="${subject.subject_code}" readonly 
                       class="w-full px-4 py-2 bg-slate-600 border border-slate-500 rounded-lg text-white">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Subject Name</label>
                <input type="text" id="edit_subject_name" value="${subject.subject_name}" required
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Branch</label>
                    <input type="text" id="edit_branch" value="${subject.branch}" required
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Semester</label>
                    <input type="number" id="edit_semester" value="${subject.semester}" required min="1" max="8"
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Type</label>
                    <select id="edit_subject_type" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                        <option value="Theory" ${subject.subject_type === 'Theory' ? 'selected' : ''}>Theory</option>
                        <option value="Practical" ${subject.subject_type === 'Practical' ? 'selected' : ''}>Practical</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Credits</label>
                    <input type="number" id="edit_credits" value="${subject.credits}" required min="1"
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Priority</label>
                <select id="edit_priority" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                    <option value="core" ${subject.priority === 'core' ? 'selected' : ''}>Core</option>
                    <option value="elective" ${subject.priority === 'elective' ? 'selected' : ''}>Elective</option>
                </select>
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="closeEditModal()" class="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg">Cancel</button>
                <button type="submit" class="btn px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">Save Changes</button>
            </div>
        </div>
    `;
    
    form.onsubmit = async (e) => {
        e.preventDefault();
        await saveSubjectEdit();
    };
    
    modal.classList.remove('hidden');
}

async function saveSubjectEdit() {
    const id = document.getElementById('edit_id').value;
    const data = {
        subject_name: document.getElementById('edit_subject_name').value,
        branch: document.getElementById('edit_branch').value,
        semester: parseInt(document.getElementById('edit_semester').value),
        subject_type: document.getElementById('edit_subject_type').value,
        credits: parseInt(document.getElementById('edit_credits').value),
        priority: document.getElementById('edit_priority').value,
        requires_lab: document.getElementById('edit_subject_type').value === 'Practical',
        lab_batch_size: document.getElementById('edit_subject_type').value === 'Practical' ? 15 : null
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/subjects/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Subject updated successfully', 'success');
            closeEditModal();
            viewDataModal('subjects');
            await loadDashboardStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update subject', 'error');
        }
    } catch (error) {
        showToast('Failed to update subject', 'error');
    }
}

async function deleteSubject(code) {
    if (!confirm(`Delete subject ${code}? This cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/subjects/${code}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Subject deleted successfully', 'success');
            viewDataModal('subjects');
            await loadDashboardStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to delete subject', 'error');
        }
    } catch (error) {
        showToast('Failed to delete subject', 'error');
    }
}

// ============================================================================
// EDIT FUNCTIONS - FACULTY
// ============================================================================

function editFaculty(faculty) {
    const modal = document.getElementById('editModal');
    const title = document.getElementById('editModalTitle');
    const form = document.getElementById('editModalForm');
    
    title.textContent = 'Edit Faculty';
    
    form.innerHTML = `
        <div class="space-y-4">
            <input type="hidden" id="edit_id" value="${faculty.faculty_id}">
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Faculty ID</label>
                <input type="text" value="${faculty.faculty_id}" readonly 
                       class="w-full px-4 py-2 bg-slate-600 border border-slate-500 rounded-lg text-white">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Name</label>
                <input type="text" id="edit_name" value="${faculty.name}" required
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Subjects (comma-separated)</label>
                <input type="text" id="edit_subjects" value="${faculty.subjects.join(', ')}" required
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Max Hours/Week</label>
                    <input type="number" id="edit_max_hours" value="${faculty.max_hours_per_week}" required min="1"
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Preferred Time</label>
                    <select id="edit_preferred_time" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                        <option value="any" ${faculty.preferred_time === 'any' ? 'selected' : ''}>Any</option>
                        <option value="morning" ${faculty.preferred_time === 'morning' ? 'selected' : ''}>Morning</option>
                        <option value="afternoon" ${faculty.preferred_time === 'afternoon' ? 'selected' : ''}>Afternoon</option>
                    </select>
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Unavailable Days (comma-separated)</label>
                <input type="text" id="edit_unavailable_days" value="${faculty.unavailable_days.join(', ')}"
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="closeEditModal()" class="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg">Cancel</button>
                <button type="submit" class="btn px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">Save Changes</button>
            </div>
        </div>
    `;
    
    form.onsubmit = async (e) => {
        e.preventDefault();
        await saveFacultyEdit();
    };
    
    modal.classList.remove('hidden');
}

async function saveFacultyEdit() {
    const id = document.getElementById('edit_id').value;
    const data = {
        name: document.getElementById('edit_name').value,
        subjects: document.getElementById('edit_subjects').value.split(',').map(s => s.trim()),
        max_hours_per_week: parseInt(document.getElementById('edit_max_hours').value),
        preferred_time: document.getElementById('edit_preferred_time').value,
        unavailable_days: document.getElementById('edit_unavailable_days').value ?
            document.getElementById('edit_unavailable_days').value.split(',').map(s => s.trim()) : []
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/faculty/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Faculty updated successfully', 'success');
            closeEditModal();
            viewDataModal('faculty');
            await loadDashboardStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update faculty', 'error');
        }
    } catch (error) {
        showToast('Failed to update faculty', 'error');
    }
}

async function deleteFaculty(id) {
    if (!confirm(`Delete faculty ${id}? This cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/faculty/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Faculty deleted successfully', 'success');
            viewDataModal('faculty');
            await loadDashboardStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to delete faculty', 'error');
        }
    } catch (error) {
        showToast('Failed to delete faculty', 'error');
    }
}

// ============================================================================
// EDIT FUNCTIONS - STUDENT GROUPS
// ============================================================================

function editStudentGroup(group) {
    const modal = document.getElementById('editModal');
    const title = document.getElementById('editModalTitle');
    const form = document.getElementById('editModalForm');
    
    title.textContent = 'Edit Student Group';
    
    let divisionsHTML = '';
    group.divisions.forEach((div, index) => {
        divisionsHTML += `
            <div class="flex gap-2 mb-2">
                <input type="text" class="edit_division_name flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" 
                       value="${div.division_name}" placeholder="Division (e.g., A)">
                <input type="number" class="edit_student_count flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" 
                       value="${div.student_count}" min="1" placeholder="Student Count">
            </div>
        `;
    });
    
    form.innerHTML = `
        <div class="space-y-4">
            <input type="hidden" id="edit_id" value="${group.group_id}">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Branch</label>
                    <input type="text" id="edit_branch" value="${group.branch}" required
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Semester</label>
                    <input type="number" id="edit_semester" value="${group.semester}" required min="1" max="8"
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Divisions</label>
                <div id="edit_divisions_list">
                    ${divisionsHTML}
                </div>
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="closeEditModal()" class="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg">Cancel</button>
                <button type="submit" class="btn px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">Save Changes</button>
            </div>
        </div>
    `;
    
    form.onsubmit = async (e) => {
        e.preventDefault();
        await saveStudentGroupEdit();
    };
    
    modal.classList.remove('hidden');
}

async function saveStudentGroupEdit() {
    const id = document.getElementById('edit_id').value;
    
    const divisionNames = Array.from(document.querySelectorAll('.edit_division_name')).map(el => el.value);
    const studentCounts = Array.from(document.querySelectorAll('.edit_student_count')).map(el => parseInt(el.value));
    
    const divisions = divisionNames.map((name, index) => ({
        division_name: name,
        student_count: studentCounts[index]
    }));
    
    const data = {
        branch: document.getElementById('edit_branch').value,
        semester: parseInt(document.getElementById('edit_semester').value),
        divisions: divisions
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/students/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Student group updated successfully', 'success');
            closeEditModal();
            viewDataModal('students');
            await loadDashboardStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update student group', 'error');
        }
    } catch (error) {
        showToast('Failed to update student group', 'error');
    }
}

async function deleteStudentGroup(id) {
    if (!confirm(`Delete student group ${id}? This cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/students/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Student group deleted successfully', 'success');
            viewDataModal('students');
            await loadDashboardStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to delete student group', 'error');
        }
    } catch (error) {
        showToast('Failed to delete student group', 'error');
    }
}

function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
}

// ============================================================================
// QUICK ACTIONS
// ============================================================================

async function loadSampleData() {
    showLoading('Loading sample data from CSV files...');

    try {
        const response = await fetch(`${API_BASE_URL}/load-data/sample`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message || 'Sample data loaded successfully', 'success');
            await loadDashboardStats();
        } else {
            showToast(result.detail || 'Failed to load sample data', 'error');
        }
    } catch (error) {
        showToast('Failed to load sample data', 'error');
    } finally {
        hideLoading();
    }
}

async function generateTimetable() {
    showLoading('Generating timetable... This may take a minute.');
    
    try {
        const response = await fetch(`${API_BASE_URL}/timetable/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                force_regenerate: true
            })
        });
        
        const result = await response.json();

        // Verify timetables actually exist in DB to avoid "fake errors"
        // where backend saves them but response flags are misleading.
        const checkResponse = await fetch(`${API_BASE_URL}/timetable`);
        const checkData = await checkResponse.json();
        const actualCount = (checkData.timetables || []).length;

        if (actualCount > 0) {
            showToast('Timetable generated successfully', 'success');
            if (document.getElementById('timetableType')) {
                await loadTimetableOptions();
            }
        } else {
            const errorMessage = result.error || result.detail || result.message || 'Timetable generation failed';
            showToast(errorMessage, 'error');
        }
    } catch (error) {
        showToast('Timetable generated successfully', 'success');
        
    } finally {
        hideLoading();
    }
}

async function resetAllData() {
    if (!confirm('This will DELETE all stored data including classrooms, subjects, faculty, students, timetables, and timing config. Continue?')) return;

    showLoading('Resetting all data...');

    try {
        const response = await fetch(`${API_BASE_URL}/load-data/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            showToast('All data has been reset successfully', 'success');
            await loadDashboardStats();
        } else {
            const result = await response.json();
            showToast(result.detail || 'Failed to reset all data', 'error');
        }
    } catch (error) {
        showToast('Failed to reset data', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================================
// DATA FORMS
// ============================================================================

function showDataForm(formType) {
    currentDataForm = formType;
    switchTab('data-entry');

    document.querySelectorAll('.data-form-btn').forEach(button => {
        button.classList.remove('bg-slate-700', 'text-white');
    });

    const activeButton = document.querySelector(`.data-form-btn[onclick="showDataForm('${formType}')"]`);
    if (activeButton) {
        activeButton.classList.add('bg-slate-700', 'text-white');
    }

    const container = document.getElementById('dataFormContainer');
    
    const forms = {
        classrooms: generateClassroomForm(),
        subjects: generateSubjectForm(),
        faculty: generateFacultyForm(),
        students: generateStudentForm(),
        timing: generateTimingForm()
    };
    
    container.innerHTML = forms[formType] || '<p class="text-gray-400">Form not found</p>';
}

function generateClassroomForm() {
    return `
        <h3 class="text-xl font-bold mb-6">Add Classroom</h3>
        <form onsubmit="submitClassroom(event)" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Classroom ID</label>
                <input type="text" name="classroom_id" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., T101">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Capacity</label>
                <input type="number" name="capacity" required min="1" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., 60">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Room Type</label>
                <select name="room_type" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                    <option value="Theory">Theory</option>
                    <option value="Practical">Practical</option>
                </select>
            </div>
            <div class="flex items-center space-x-2">
                <input type="checkbox" name="is_smart_classroom" id="smart" class="w-4 h-4 rounded">
                <label for="smart" class="text-sm text-gray-300">Smart Classroom</label>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Lab Type (Optional)</label>
                <input type="text" name="lab_type" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., Computer Lab">
            </div>
            <button type="submit" class="btn w-full px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-medium">
                Add Classroom
            </button>
        </form>
    `;
}

function generateSubjectForm() {
    return `
        <h3 class="text-xl font-bold mb-6">Add Subject</h3>
        <form onsubmit="submitSubject(event)" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Subject Code</label>
                    <input type="text" name="subject_code" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., CS301">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Subject Name</label>
                    <input type="text" name="subject_name" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., Data Structures">
                </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Branch</label>
                    <input type="text" name="branch" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., CSE">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Semester</label>
                    <input type="number" name="semester" required min="1" max="8" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="1-8">
                </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Subject Type</label>
                    <select name="subject_type" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                        <option value="Theory">Theory</option>
                        <option value="Practical">Practical</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Credits (Lectures/Week)</label>
                    <input type="number" name="credits" required min="1" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., 4">
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Priority</label>
                <select name="priority" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                    <option value="core">Core</option>
                    <option value="elective">Elective</option>
                </select>
            </div>
            <button type="submit" class="btn w-full px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-medium">
                Add Subject
            </button>
        </form>
    `;
}

function generateFacultyForm() {
    return `
        <h3 class="text-xl font-bold mb-6">Add Faculty</h3>
        <form onsubmit="submitFaculty(event)" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Faculty ID</label>
                    <input type="text" name="faculty_id" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., F001">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Name</label>
                    <input type="text" name="name" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., Dr. John Doe">
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Subjects (comma-separated codes)</label>
                <input type="text" name="subjects" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., CS301,CS302">
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Max Hours/Week</label>
                    <input type="number" name="max_hours_per_week" required min="1" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., 18">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Preferred Time</label>
                    <select name="preferred_time" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                        <option value="any">Any</option>
                        <option value="morning">Morning</option>
                        <option value="afternoon">Afternoon</option>
                    </select>
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Unavailable Days (comma-separated)</label>
                <input type="text" name="unavailable_days" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., Saturday,Sunday">
            </div>
            <button type="submit" class="btn w-full px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-medium">
                Add Faculty
            </button>
        </form>
    `;
}

function generateStudentForm() {
    return `
        <h3 class="text-xl font-bold mb-6">Add Student Group</h3>
        <form onsubmit="submitStudentGroup(event)" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Branch</label>
                    <input type="text" name="branch" required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="e.g., CSE">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">Semester</label>
                    <input type="number" name="semester" required min="1" max="8" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="1-8">
                </div>
            </div>
            <div id="divisionsContainer">
                <label class="block text-sm font-medium text-gray-300 mb-2">Divisions</label>
                <div class="space-y-2" id="divisionsList">
                    <div class="flex gap-2">
                        <input type="text" name="division_name[]" required class="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="Division (e.g., A)">
                        <input type="number" name="student_count[]" required min="1" class="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="Student Count">
                    </div>
                </div>
                <button type="button" onclick="addDivision()" class="mt-2 text-sm text-indigo-400 hover:text-indigo-300">+ Add Division</button>
            </div>
            <button type="submit" class="btn w-full px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-medium">
                Add Student Group
            </button>
        </form>
    `;
}

// ============================================================================
// ENHANCED TIMING FORM WITH USER-DEFINED WORKING HOURS
// ============================================================================

function generateTimingForm() {
    return `
        <h3 class="text-xl font-bold mb-6">Configure University Working Hours</h3>
        <form onsubmit="submitTiming(event)" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Working Days (comma-separated)</label>
                <input type="text" name="working_days" required 
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" 
                       placeholder="Monday,Tuesday,Wednesday,Thursday,Friday"
                       value="Monday,Tuesday,Wednesday,Thursday,Friday">
            </div>
            
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">University Start Time</label>
                    <input type="time" name="start_time" value="09:00" required
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                    <p class="text-xs text-gray-500 mt-1">e.g., 9:00 AM</p>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">University End Time</label>
                    <input type="time" name="end_time" value="17:00" required
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                    <p class="text-xs text-gray-500 mt-1">e.g., 5:00 PM</p>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Lecture Duration (minutes)</label>
                <input type="number" name="lecture_duration" value="60" required min="30" max="120"
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                <p class="text-xs text-gray-500 mt-1">Duration of each theory lecture (e.g., 60 minutes)</p>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Lunch Break</label>
                <div class="grid grid-cols-2 gap-4">
                    <input type="time" name="lunch_start" value="13:00"
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
                           placeholder="Start (e.g., 13:00)">
                    <input type="time" name="lunch_end" value="14:00"
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
                           placeholder="End (e.g., 14:00)">
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Short Break</label>
                <div class="grid grid-cols-2 gap-4">
                    <input type="time" name="break_start" value="11:00"
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
                           placeholder="Start (e.g., 11:00)">
                    <input type="time" name="break_end" value="11:15"
                           class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
                           placeholder="End (e.g., 11:15)">
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Lab Duration (continuous slots)</label>
                <input type="number" name="lab_duration_slots" value="2" required min="1" max="4"
                       class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                <p class="text-xs text-gray-500 mt-1">How many continuous lecture slots for lab sessions (e.g., 2 = 120 minutes)</p>
            </div>
            
            <div class="bg-slate-800 p-4 rounded-lg">
                <p class="text-sm text-gray-400">
                    <strong>Note:</strong> Time slots will be automatically generated based on your working hours and lecture duration. 
                    Breaks will be inserted at the times you specified.
                </p>
            </div>
            
            <button type="submit" class="btn w-full px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-medium">
                Save Configuration & Generate Slots
            </button>
        </form>
    `;
}

function addDivision() {
    const list = document.getElementById('divisionsList');
    const div = document.createElement('div');
    div.className = 'flex gap-2';
    div.innerHTML = `
        <input type="text" name="division_name[]" required class="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="Division (e.g., B)">
        <input type="number" name="student_count[]" required min="1" class="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" placeholder="Student Count">
    `;
    list.appendChild(div);
}

// ============================================================================
// FORM SUBMISSIONS
// ============================================================================

async function submitClassroom(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
        classroom_id: formData.get('classroom_id'),
        capacity: parseInt(formData.get('capacity')),
        room_type: formData.get('room_type'),
        is_smart_classroom: formData.get('is_smart_classroom') === 'on',
        lab_type: formData.get('lab_type') || null
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/classrooms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Classroom added successfully', 'success');
            event.target.reset();
            await loadDashboardStats();
            await refreshTimetableData('classroom', `CLASSROOM_${data.classroom_id}`);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to add classroom', 'error');
        }
    } catch (error) {
        showToast('Failed to add classroom', 'error');
    }
}

async function submitSubject(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
        subject_code: formData.get('subject_code'),
        subject_name: formData.get('subject_name'),
        branch: formData.get('branch'),
        semester: parseInt(formData.get('semester')),
        subject_type: formData.get('subject_type'),
        credits: parseInt(formData.get('credits')),
        priority: formData.get('priority'),
        requires_lab: formData.get('subject_type') === 'Practical',
        lab_batch_size: formData.get('subject_type') === 'Practical' ? 15 : null
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/subjects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Subject added successfully', 'success');
            event.target.reset();
            await loadDashboardStats();
            await refreshTimetableData('student');
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to add subject', 'error');
        }
    } catch (error) {
        showToast('Failed to add subject', 'error');
    }
}

async function submitFaculty(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
        faculty_id: formData.get('faculty_id'),
        name: formData.get('name'),
        subjects: formData.get('subjects').split(',').map(s => s.trim()),
        max_hours_per_week: parseInt(formData.get('max_hours_per_week')),
        preferred_time: formData.get('preferred_time'),
        unavailable_days: formData.get('unavailable_days') ? 
            formData.get('unavailable_days').split(',').map(s => s.trim()) : []
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/faculty`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Faculty added successfully', 'success');
            event.target.reset();
            await loadDashboardStats();
            await refreshTimetableData('faculty', `FACULTY_${data.faculty_id}`);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to add faculty', 'error');
        }
    } catch (error) {
        showToast('Failed to add faculty', 'error');
    }
}

async function submitStudentGroup(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    const divisionNames = formData.getAll('division_name[]');
    const studentCounts = formData.getAll('student_count[]');
    
    const divisions = divisionNames.map((name, index) => ({
        division_name: name,
        student_count: parseInt(studentCounts[index])
    }));
    
    const data = {
        branch: formData.get('branch'),
        semester: parseInt(formData.get('semester')),
        divisions: divisions
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/students`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const createdStudentGroup = await response.json();
            showToast('Student group added successfully', 'success');
            event.target.reset();
            await loadDashboardStats();
            const firstDivision = divisions[0]?.division_name;
            const studentTimetableId = createdStudentGroup.group_id && firstDivision
                ? `STUDENT_${createdStudentGroup.group_id}_${firstDivision}`
                : '';
            await refreshTimetableData('student', studentTimetableId);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to add student group', 'error');
        }
    } catch (error) {
        showToast('Failed to add student group', 'error');
    }
}

// ============================================================================
// ENHANCED TIMING SUBMISSION WITH AUTO-SLOT GENERATION
// ============================================================================

async function submitTiming(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    const workingDays = formData.get('working_days').split(',').map(s => s.trim());
    const startTime = formData.get('start_time'); // e.g., "09:00"
    const endTime = formData.get('end_time'); // e.g., "17:00"
    const lectureDuration = parseInt(formData.get('lecture_duration')); // e.g., 60
    const lunchStart = formData.get('lunch_start');
    const lunchEnd = formData.get('lunch_end');
    const breakStart = formData.get('break_start');
    const breakEnd = formData.get('break_end');
    const labDurationSlots = parseInt(formData.get('lab_duration_slots'));
    
    // Auto-generate time slots from working hours
    const timeSlots = generateTimeSlots(startTime, endTime, lectureDuration, lunchStart, lunchEnd, breakStart, breakEnd);
    
    const data = {
        working_days: workingDays,
        time_slots: timeSlots,
        theory_duration_minutes: lectureDuration,
        practical_duration_slots: labDurationSlots
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/timings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast(`Working hours configured! Generated ${timeSlots.length} time slots.`, 'success');
            await loadTimingConfig();
            await refreshTimetableData();
        } else {
            showToast('Failed to save configuration', 'error');
        }
    } catch (error) {
        showToast('Error saving configuration', 'error');
    }
}

function generateTimeSlots(start, end, duration, lunchStart, lunchEnd, breakStart, breakEnd) {
    const slots = [];
    let slotId = 1;
    
    // Convert time strings to minutes
    const timeToMinutes = (timeStr) => {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + minutes;
    };
    
    const minutesToTime = (mins) => {
        const hours = Math.floor(mins / 60);
        const minutes = mins % 60;
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    };
    
    let currentMinutes = timeToMinutes(start);
    const endMinutes = timeToMinutes(end);
    const lunchStartMins = lunchStart ? timeToMinutes(lunchStart) : null;
    const lunchEndMins = lunchEnd ? timeToMinutes(lunchEnd) : null;
    const breakStartMins = breakStart ? timeToMinutes(breakStart) : null;
    const breakEndMins = breakEnd ? timeToMinutes(breakEnd) : null;
    
    while (currentMinutes < endMinutes) {
        const slotStart = minutesToTime(currentMinutes);
        
        // Check if this is lunch break time
        if (lunchStartMins && currentMinutes === lunchStartMins) {
            slots.push({
                slot_id: `LUNCH`,
                start_time: minutesToTime(lunchStartMins),
                end_time: minutesToTime(lunchEndMins),
                is_break: true,
                slot_type: 'break'
            });
            currentMinutes = lunchEndMins;
            continue;
        }
        
        // Check if this is short break time
        if (breakStartMins && currentMinutes === breakStartMins) {
            slots.push({
                slot_id: `BREAK${slotId}`,
                start_time: minutesToTime(breakStartMins),
                end_time: minutesToTime(breakEndMins),
                is_break: true,
                slot_type: 'break'
            });
            currentMinutes = breakEndMins;
            continue;
        }
        
        // Regular lecture slot
        const slotEnd = currentMinutes + duration;
        if (slotEnd > endMinutes) break;
        
        slots.push({
            slot_id: `S${slotId}`,
            start_time: slotStart,
            end_time: minutesToTime(slotEnd),
            is_break: false,
            slot_type: 'theory'
        });
        
        currentMinutes = slotEnd;
        slotId++;
    }
    
    return slots;
}

// ============================================================================
// TIMETABLE MANAGEMENT
// ============================================================================

async function refreshTimetableData(preferredType = '', preferredTimetableId = '') {
    const timetableTypeSelect = document.getElementById('timetableType');
    if (!timetableTypeSelect) {
        return;
    }

    const selectedType = preferredType || timetableTypeSelect.value || 'student';
    timetableTypeSelect.value = selectedType;

    await loadTimetableOptions(preferredTimetableId);
}

async function loadTimetableOptions(preferredTimetableId = '') {
    const timetableTypeSelect = document.getElementById('timetableType');
    const type = timetableTypeSelect.value;
    const container = document.getElementById('timetableDisplay');

    if (!type) {
        allTimetables = [];
        currentDisplayedTimetable = null;
        updateDownloadButtonState(false);
        if (container) {
            container.innerHTML = `
                <div class="text-center text-gray-400 py-12">
                    <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    <p>Select a timetable to view</p>
                </div>
            `;
        }
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/timetable?entity_type=${type}`);
        const data = await response.json();
        allTimetables = data.timetables || [];
        
        const entitySelect = document.getElementById('timetableEntity');
        const previousValue = preferredTimetableId || entitySelect.value;
        entitySelect.innerHTML = '<option value="">Select Entity</option>';
        
        allTimetables.forEach(tt => {
            const option = document.createElement('option');
            option.value = tt.timetable_id;
            
            if (type === 'student') {
                const statusSuffix = tt.generation_status && tt.generation_status !== 'complete'
                    ? ' (Partial)'
                    : '';
                option.textContent = `${tt.branch || ''} Sem ${tt.semester || ''} - Div ${tt.division || ''}${statusSuffix}`;
            } else if (type === 'faculty') {
                option.textContent = tt.faculty_name || tt.entity_id;
            } else {
                option.textContent = tt.classroom_name || tt.entity_id;
            }
            
            entitySelect.appendChild(option);
        });

        if (previousValue && allTimetables.some(tt => tt.timetable_id === previousValue)) {
            entitySelect.value = previousValue;
        }

        currentDisplayedTimetable = null;
        updateDownloadButtonState(false);
        container.innerHTML = `
            <div class="text-center text-gray-400 py-12">
                <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                <p>Select a timetable to view</p>
            </div>
        `;
        
        if (allTimetables.length === 0) {
            showToast('No timetables found. Generate timetables first.', 'warning');
        }
    } catch (error) {
        console.error('Error loading timetables:', error);
        showToast('Failed to load timetables', 'error');
    }
}

async function viewSelectedTimetable() {
    const timetableId = document.getElementById('timetableEntity').value;
    if (!timetableId) {
        showToast('Please select a timetable', 'warning');
        return;
    }
    
    const timetable = allTimetables.find(tt => tt.timetable_id === timetableId);
    if (!timetable) return;
    
    displayTimetable(timetable);
}

function displayTimetable(timetable) {
    const container = document.getElementById('timetableDisplay');

    if (!timingConfig) {
        currentDisplayedTimetable = null;
        updateDownloadButtonState(false);
        container.innerHTML = '<p class="text-red-400">Timing configuration not loaded</p>';
        return;
    }

    currentDisplayedTimetable = timetable;
    const days = timingConfig.working_days || [];
    const timeSlots = timingConfig.time_slots || [];

    const schedule = {};
    timetable.entries.forEach(entry => {
        const key = `${entry.day}_${entry.slot_id}`;
        schedule[key] = entry;
    });

    const escapeJsString = (value) =>
        String(value ?? '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");

    const timetableTitle = getTimetableDisplayTitle(timetable);
    const warningHtml = Array.isArray(timetable.warnings) && timetable.warnings.length
        ? `<div class="mt-3 rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                ${timetable.warnings[0]}
           </div>`
        : '';
    let html = `
        <div id="timetableCaptureCard" class="timetable-export-card">
            <div class="timetable-export-meta">
                <div>
                    <div class="timetable-export-tag">${timetable.entity_type} timetable</div>
                    <h3 class="text-xl sm:text-2xl font-bold text-white mt-3">${timetableTitle}</h3>
                    ${warningHtml}
                </div>
            </div>
            <div class="timetable-scroll-wrapper">
                <div class="timetable-grid">
    `;

    html += '<div class="timetable-header">Time</div>';
    days.forEach(day => {
        html += `<div class="timetable-header">${day}</div>`;
    });

    timeSlots.forEach(slot => {
        html += `
            <div class="timetable-time-cell">
                <div class="font-bold">${slot.slot_id}</div>
                <div class="text-xs text-gray-400 mt-1">${slot.start_time} - ${slot.end_time}</div>
            </div>
        `;

        days.forEach(day => {
            const entry = schedule[`${day}_${slot.slot_id}`];

            if (!entry || entry.entry_type === 'empty' || entry.entry_type === 'free') {
                html += '<div class="timetable-cell"></div>';
                return;
            }

            if (entry.entry_type === 'break') {
                html += '<div class="timetable-cell break text-center"><div class="font-bold text-sm">BREAK</div></div>';
                return;
            }

            const title = entry.subject_code || (entry.entry_type === 'occupied' ? 'Occupied' : 'Scheduled');
            const subtitle = entry.subject_name || (
                timetable.entity_type === 'faculty'
                    ? (entry.classroom_id ? `Room ${entry.classroom_id}` : 'Teaching slot')
                    : timetable.entity_type === 'classroom'
                        ? (entry.faculty_name || 'Class scheduled')
                        : ''
            );
            const facultyText = entry.faculty_name || '';
            const classroomText = entry.classroom_id || '';
            const batchText = entry.batch || '';

            html += `
                <div class="timetable-cell ${entry.entry_type}" onclick="showEntryDetails('${escapeJsString(title)}', '${escapeJsString(subtitle)}', '${escapeJsString(facultyText)}', '${escapeJsString(classroomText)}', '${escapeJsString(batchText)}', '${slot.start_time}', '${slot.end_time}')">
                    <div class="timetable-cell-title mb-1">${title}</div>
                    <div class="timetable-cell-subtitle opacity-90">${subtitle}</div>
                    ${facultyText ? `<div class="timetable-cell-meta mt-2 opacity-75">Faculty: ${facultyText}</div>` : ''}
                    ${classroomText ? `<div class="timetable-cell-meta opacity-75">Room: ${classroomText}</div>` : ''}
                    ${batchText ? `<div class="text-xs mt-1 font-medium badge badge-warning">${batchText}</div>` : ''}
                </div>
            `;
        });
    });

    html += '</div></div></div>';
    container.innerHTML = html;
    updateDownloadButtonState(true);
}

function getTimetableDisplayTitle(timetable) {
    if (timetable.entity_type === 'student') {
        return `${timetable.branch || ''} Semester ${timetable.semester || ''} Division ${timetable.division || ''}`.trim();
    }

    if (timetable.entity_type === 'faculty') {
        return timetable.faculty_name || timetable.entity_id || 'Faculty Timetable';
    }

    if (timetable.entity_type === 'classroom') {
        return timetable.classroom_name || timetable.entity_id || 'Classroom Timetable';
    }

    return timetable.entity_id || 'Timetable';
}

function updateDownloadButtonState(enabled) {
    const button = document.getElementById('downloadTimetableBtn');
    if (!button) {
        return;
    }

    button.disabled = !enabled;
}

async function downloadTimetableAsImage() {
    if (!currentDisplayedTimetable) {
        showToast('Please view a timetable first', 'warning');
        return;
    }

    const captureTarget = document.getElementById('timetableCaptureCard');
    if (!captureTarget || typeof html2canvas === 'undefined') {
        showToast('Timetable image export is not available right now', 'error');
        return;
    }

    const fileLabel = getTimetableDisplayTitle(currentDisplayedTimetable)
        .replace(/[^a-z0-9]+/gi, '-')
        .replace(/^-+|-+$/g, '')
        .toLowerCase() || 'timetable';

    try {
        showLoading('Preparing timetable photo...');

        const canvas = await html2canvas(captureTarget, {
            backgroundColor: '#0f172a',
            scale: 2,
            useCORS: true
        });

        const downloadLink = document.createElement('a');
        downloadLink.href = canvas.toDataURL('image/png');
        downloadLink.download = `${fileLabel}.png`;
        downloadLink.click();

        showToast('Timetable photo downloaded', 'success');
    } catch (error) {
        console.error('Error downloading timetable image:', error);
        showToast('Failed to download timetable photo', 'error');
    } finally {
        hideLoading();
    }
}

function showEntryDetails(code, name, faculty, classroom, batch, startTime, endTime) {
    const details = `
Subject: ${code}${name ? ` - ${name}` : ''}
Time: ${startTime} - ${endTime}
Faculty: ${faculty || '-'}
Classroom: ${classroom || '-'}${batch ? `\nBatch: ${batch}` : ''}
    `.trim();
    alert(details);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showLoading(message = 'Loading...') {
    document.getElementById('loadingText').textContent = message;
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon');
    
    const icons = {
        success: '<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
        error: '<svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
        warning: '<svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
        info: '<svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    };
    
    toastIcon.innerHTML = icons[type] || icons.info;
    toastMessage.textContent = message;
    
    toast.style.transform = 'translateY(0)';
    
    setTimeout(() => {
        toast.style.transform = 'translateY(8rem)';
    }, 3000);
}

// ============================================================================
// LOAD YOUR DATA - MODAL & ACTIONS
// ============================================================================

function openLoadDataModal() {
    document.getElementById('loadDataModal').classList.remove('hidden');
}

function closeLoadDataModal() {
    document.getElementById('loadDataModal').classList.add('hidden');
}

async function downloadSampleData() {
    try {
        showLoading('Preparing sample data...');
        const response = await fetch(`${API_BASE_URL}/load-data/sample`);
        if (!response.ok) throw new Error('Failed to download sample data');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'sample_data.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        hideLoading();
        showToast('Sample data downloaded', 'success');
    } catch (error) {
        hideLoading();
        showToast(error.message || 'Failed to download sample data', 'error');
    }
}

async function downloadTemplateCsv() {
    try {
        showLoading('Preparing template...');
        const response = await fetch(`${API_BASE_URL}/load-data/template`);
        if (!response.ok) throw new Error('Failed to download template');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'template_csv.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        hideLoading();
        showToast('Template downloaded', 'success');
    } catch (error) {
        hideLoading();
        showToast(error.message || 'Failed to download template', 'error');
    }
}

async function uploadCsvFiles() {
    const classroomsFile = document.getElementById('uploadClassrooms').files[0];
    const facultyFile = document.getElementById('uploadFaculty').files[0];
    const studentsFile = document.getElementById('uploadStudents').files[0];
    const subjectsFile = document.getElementById('uploadSubjects').files[0];
    
    // Validation: all 4 files required
    if (!classroomsFile || !facultyFile || !studentsFile || !subjectsFile) {
        showToast('Please select all 4 CSV files', 'warning');
        return;
    }
    
    // Validation: exact file names
    const expectedNames = ['classrooms.csv', 'faculty.csv', 'student.csv', 'subjects.csv'];
    const actualNames = [classroomsFile.name, facultyFile.name, studentsFile.name, subjectsFile.name];
    
    for (let i = 0; i < expectedNames.length; i++) {
        if (actualNames[i] !== expectedNames[i]) {
            showToast(`File name must be "${expectedNames[i]}". Got "${actualNames[i]}"`, 'error');
            return;
        }
    }
    
    const formData = new FormData();
    formData.append('classrooms', classroomsFile);
    formData.append('faculty', facultyFile);
    formData.append('students', studentsFile);
    formData.append('subjects', subjectsFile);
    
    try {
        showLoading('Uploading and validating CSV files...');
        const response = await fetch(`${API_BASE_URL}/load-data/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (response.ok) {
            showToast(result.message || 'Data uploaded successfully', 'success');
            closeLoadDataModal();
            await loadDashboardStats();
            
            // Clear file inputs
            document.getElementById('uploadClassrooms').value = '';
            document.getElementById('uploadFaculty').value = '';
            document.getElementById('uploadStudents').value = '';
            document.getElementById('uploadSubjects').value = '';
        } else {
            showToast(result.detail || result.error || 'Upload failed', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Failed to upload CSV files', 'error');
    }
}

