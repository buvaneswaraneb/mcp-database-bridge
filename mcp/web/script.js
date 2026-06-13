document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide Icons
    lucide.createIcons();

    // Elements
    const themeToggle = document.getElementById('themeToggle');
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const refreshBtn = document.getElementById('refreshBtn');
    const dbGrid = document.getElementById('dbGrid');
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const toast = document.getElementById('toast');

    let isDarkTheme = false;

    // Theme Management
    themeToggle.addEventListener('click', () => {
        isDarkTheme = !isDarkTheme;
        document.body.className = isDarkTheme ? 'dark-theme' : 'light-theme';
        const icon = isDarkTheme ? 'sun' : 'moon';
        themeToggle.innerHTML = `<i data-lucide="${icon}"></i>`;
        lucide.createIcons();
    });

    // Helper: Format Bytes
    function formatBytes(bytes, decimals = 2) {
        if (!+bytes) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
    }

    // Helper: Show Toast
    function showToast(message, type = 'success') {
        const icon = type === 'success' ? 'check-circle' : 'alert-circle';
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i data-lucide="${icon}"></i> <span>${message}</span>`;
        lucide.createIcons();
        
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Fetch Databases
    async function loadDatabases() {
        dbGrid.innerHTML = '';
        emptyState.classList.add('hidden');
        loadingState.classList.remove('hidden');

        try {
            const res = await fetch('/api/databases');
            if (!res.ok) throw new Error('Failed to fetch databases');
            
            const databases = await res.json();
            loadingState.classList.add('hidden');

            if (databases.length === 0) {
                emptyState.classList.remove('hidden');
            } else {
                renderDatabases(databases);
            }
        } catch (error) {
            console.error(error);
            loadingState.classList.add('hidden');
            showToast(error.message, 'error');
        }
    }

    // Render Database Cards
    function renderDatabases(databases) {
        databases.forEach(db => {
            const card = document.createElement('div');
            card.className = 'db-card';
            
            card.innerHTML = `
                <div class="db-info">
                    <i data-lucide="database" class="db-icon"></i>
                    <div class="db-details">
                        <h3>${db.name}</h3>
                        <p>${formatBytes(db.size)}</p>
                    </div>
                </div>
                <div class="db-actions">
                    <button class="delete-btn" data-name="${db.name}" title="Delete database">
                        <i data-lucide="trash-2"></i> Delete
                    </button>
                </div>
            `;
            
            dbGrid.appendChild(card);
        });

        lucide.createIcons();

        // Attach delete listeners
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.currentTarget.getAttribute('data-name');
                deleteDatabase(name);
            });
        });
    }

    // Upload Logic
    async function uploadFile(file) {
        if (!file.name.endsWith('.db') && !file.name.endsWith('.sqlite')) {
            showToast('Only .db and .sqlite files are allowed', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/databases/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            
            if (!res.ok) {
                throw new Error(data.detail || 'Upload failed');
            }

            showToast(data.message, 'success');
            loadDatabases();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    // Delete Logic
    async function deleteDatabase(name) {
        if (!confirm(`Are you sure you want to delete '${name}'? This action cannot be undone.`)) {
            return;
        }

        try {
            const res = await fetch(`/api/databases/${encodeURIComponent(name)}`, {
                method: 'DELETE'
            });

            const data = await res.json();
            
            if (!res.ok) {
                throw new Error(data.detail || 'Deletion failed');
            }

            showToast(data.message, 'success');
            loadDatabases();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    // Event Listeners for Drag & Drop and Upload
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
            fileInput.value = ''; // Reset
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });

    refreshBtn.addEventListener('click', loadDatabases);

    // Initial Load
    loadDatabases();
});
