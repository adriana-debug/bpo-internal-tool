// Employee Directory JavaScript Module
class EmployeeDirectory {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 50;
        this.totalPages = 1;
        this.selectedEmployees = new Set();
        this.editingEmployee = null;
        this.filterOptions = {};
        
        // Sorting state
        this.sortColumn = 'full_name';
        this.sortOrder = 'asc';
        
        this.init();
    }

    init() {
        this.loadFilterOptions();
        this.loadEmployeeStatistics();
        this.loadEmployees();
        this.initEventListeners();
        this.updateActiveFilterCount();
    }

    initEventListeners() {
        // Search input with debounce
        let searchTimeout;
        document.getElementById('searchInput')?.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.currentPage = 1;
                this.loadEmployees();
                this.updateFilteredStatistics();
                this.updateActiveFilterCount();
            }, 300);
        });

        // Form submission
        document.getElementById('employeeForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveEmployee();
        });

        // Filter changes
        ['departmentFilter', 'campaignFilter', 'statusFilter'].forEach(id => {
            document.getElementById(id)?.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadEmployees();
                this.updateFilteredStatistics();
                this.updateActiveFilterCount();
            });
        });
    }

    attachHeaderClickHandlers() {
        // Attach click handlers to table headers for sorting
        const headers = document.querySelectorAll('thead th');
        console.log(`Attaching click handlers to ${headers.length} headers`);
        
        headers.forEach((header, index) => {
            // Skip Action column (last column)
            if (index === headers.length - 1) return;
            
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                const columnName = this.getColumnNameFromIndex(index);
                console.log(`Header ${index} clicked: ${columnName}`);
                this.handleSort(columnName);
            });
        });
    }

    getColumnNameFromIndex(index) {
        const columnMapping = [
            'full_name',      // 0: Name
            'campaign',       // 1: Campaign
            'date_of_joining', // 2: Date of Joining
            'last_working_date', // 3: Last Working Date
            'employee_status', // 4: Status
            'phone_no'        // 5: Phone No.
        ];
        return columnMapping[index] || 'full_name';
    }

    handleSort(columnName) {
        if (this.sortColumn === columnName) {
            // Toggle sort order if same column clicked
            this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            // New column, default to ascending
            this.sortColumn = columnName;
            this.sortOrder = 'asc';
        }
        
        console.log(`Sorting by ${this.sortColumn} (${this.sortOrder})`);
        this.currentPage = 1;
        this.loadEmployees();
    }

    updateSortIndicators() {
        // Remove all sort indicator spans
        document.querySelectorAll('thead th .sort-indicator').forEach(indicator => {
            indicator.remove();
        });
        
        // Add indicator to current sort column
        const headers = document.querySelectorAll('thead th');
        const columnIndex = this.getColumnIndexFromName(this.sortColumn);
        if (columnIndex !== -1 && columnIndex < headers.length) {
            const header = headers[columnIndex];
            const indicator = document.createElement('span');
            indicator.className = 'sort-indicator';
            indicator.textContent = this.sortOrder === 'asc' ? ' ▲' : ' ▼';
            header.appendChild(indicator);
        }
    }

    getColumnIndexFromName(columnName) {
        const columnMapping = [
            'full_name',
            'campaign',
            'date_of_joining',
            'last_working_date',
            'employee_status',
            'phone_no'
        ];
        return columnMapping.indexOf(columnName);
    }

    async loadFilterOptions() {
        try {
            const response = await fetch('/api/employees/filter-options');
            this.filterOptions = await response.json();
            
            this.populateFilterDropdowns();
        } catch (error) {
            console.error('Error loading filter options:', error);
            this.showToast('Error loading filter options', 'error');
        }
    }

    populateFilterDropdowns() {
        // Populate department filter
        const deptSelect = document.getElementById('departmentFilter');
        if (deptSelect && this.filterOptions.departments) {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            this.filterOptions.departments.forEach(dept => {
                deptSelect.innerHTML += `<option value="${dept}">${dept}</option>`;
            });
        }

        // Populate campaign filter
        const campaignSelect = document.getElementById('campaignFilter');
        if (campaignSelect && this.filterOptions.campaigns) {
            campaignSelect.innerHTML = '<option value="">All Campaigns</option>';
            this.filterOptions.campaigns.forEach(campaign => {
                campaignSelect.innerHTML += `<option value="${campaign}">${campaign}</option>`;
            });
        }

        // Populate status filter
        const statusSelect = document.getElementById('statusFilter');
        if (statusSelect && this.filterOptions.statuses) {
            statusSelect.innerHTML = '<option value="">All Statuses</option>';
            this.filterOptions.statuses.forEach(status => {
                statusSelect.innerHTML += `<option value="${status}">${status}</option>`;
            });
        }

        // Populate role dropdown in modal
        const roleSelect = document.getElementById('roleName');
        if (roleSelect && this.filterOptions.roles) {
            roleSelect.innerHTML = '<option value="">Select Role</option>';
            this.filterOptions.roles.forEach(role => {
                roleSelect.innerHTML += `<option value="${role.name}">${role.display_name}</option>`;
            });
        }
    }

    async loadEmployeeStatistics() {
        try {
            const response = await fetch('/api/employees/statistics');
            const stats = await response.json();
            
            // Update KPI cards
            document.getElementById('totalEmployees').textContent = stats.total_employees || 0;
            document.getElementById('activeEmployees').textContent = stats.active_employees || 0;
            
            const activePercentage = stats.total_employees > 0 
                ? Math.round((stats.active_employees / stats.total_employees) * 100) 
                : 0;
            document.getElementById('activePercentage').textContent = `${activePercentage}% active rate`;
            
            // Calculate new hires (from status breakdown dictionary)
            const newHires = stats.status_breakdown?.['New Hire'] || 0;
            document.getElementById('newHires').textContent = newHires;
            
            // Count unique departments
            document.getElementById('totalDepartments').textContent = 
                Object.keys(stats.department_breakdown || {}).length;
                
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    async updateFilteredStatistics() {
        try {
            // Build filter parameters
            const params = new URLSearchParams();

            const search = document.getElementById('searchInput')?.value;
            if (search) params.append('search', search);

            const department = document.getElementById('departmentFilter')?.value;
            if (department) params.append('department', department);

            const campaign = document.getElementById('campaignFilter')?.value;
            if (campaign) params.append('campaign', campaign);

            const status = document.getElementById('statusFilter')?.value;
            if (status) params.append('employee_status', status);

            // Fetch all filtered employees (no pagination limit for stats)
            const response = await fetch(`/api/employees?${params}&limit=10000`);
            if (!response.ok) throw new Error('Failed to fetch employees for statistics');
            
            const data = await response.json();
            const employees = data.employees || [];
            
            // Calculate filtered statistics
            const totalEmployees = employees.length;
            const activeEmployees = employees.filter(emp => emp.employee_status === 'Active').length;
            const activePercentage = totalEmployees > 0 
                ? Math.round((activeEmployees / totalEmployees) * 100) 
                : 0;
            
            // Count new hires
            const newHires = employees.filter(emp => emp.employee_status === 'New Hire').length;
            
            // Count unique departments
            const uniqueDepartments = new Set(employees.map(emp => emp.department)).size;
            
            // Update KPI cards
            document.getElementById('totalEmployees').textContent = totalEmployees;
            document.getElementById('activeEmployees').textContent = activeEmployees;
            document.getElementById('activePercentage').textContent = `${activePercentage}% active rate`;
            document.getElementById('newHires').textContent = newHires;
            document.getElementById('totalDepartments').textContent = uniqueDepartments;
                
        } catch (error) {
            console.error('Error updating filtered statistics:', error);
        }
    }

    async loadEmployees() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.pageSize,
                sort_by: this.sortColumn,
                sort_order: this.sortOrder
            });

            // Add filters
            const search = document.getElementById('searchInput')?.value;
            if (search) params.append('search', search);

            const department = document.getElementById('departmentFilter')?.value;
            if (department) params.append('department', department);

            const campaign = document.getElementById('campaignFilter')?.value;
            if (campaign) params.append('campaign', campaign);

            const status = document.getElementById('statusFilter')?.value;
            if (status) params.append('employee_status', status);

            const response = await fetch(`/api/employees?${params}`);
            if (!response.ok) throw new Error('Failed to fetch employees');
            
            const data = await response.json();
            
            this.renderEmployeeTable(data.employees);
            this.renderPagination(data);
            this.updateRecordCount(data);
            this.updateSortIndicators();
            
        } catch (error) {
            console.error('Error loading employees:', error);
            this.showToast('Error loading employees', 'error');
            document.getElementById('employeeTableBody').innerHTML = 
                '<tr><td colspan="14" class="px-6 py-4 text-center text-red-500">Error loading employees</td></tr>';
        }
    }

    renderEmployeeTable(employees) {
        const tbody = document.getElementById('employeeTableBody');
        if (!tbody) return;

        if (employees.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-8 text-center text-gray-500">
                        <iconify-icon icon="solar:users-group-rounded-bold-duotone" class="text-4xl text-gray-300 mx-auto mb-3"></iconify-icon>
                        <p>No employees found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = employees.map(emp => {
            const statusColor = this.getStatusColor(emp.employee_status);
            
            return `
                <tr class="hover:bg-gray-50 cursor-pointer transition-colors" onclick="employeeDirectory.openEmployeeDrawer(${emp.id})">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mr-3">
                                <span class="text-xs font-medium text-primary">${emp.full_name.charAt(0)}</span>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-gray-900">${emp.full_name}</div>
                                <div class="text-xs text-gray-500">${emp.employee_no}</div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${emp.campaign || '-'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${emp.date_of_joining ? this.formatDate(emp.date_of_joining) : '-'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${emp.last_working_date ? this.formatDate(emp.last_working_date) : '-'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColor}">
                            ${emp.employee_status}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${emp.phone_no || '-'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div class="flex items-center gap-2" onclick="event.stopPropagation()">
                            <button onclick="employeeDirectory.editEmployee(${emp.id})" 
                                    class="text-primary hover:text-primary/80 transition-colors" title="Edit">
                                <iconify-icon icon="solar:pen-bold" class="text-lg"></iconify-icon>
                            </button>
                            <button onclick="employeeDirectory.deleteEmployee(${emp.id})" 
                                    class="text-red-600 hover:text-red-800 transition-colors" title="Delete">
                                <iconify-icon icon="solar:trash-bin-minimalistic-bold" class="text-lg"></iconify-icon>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Attach header click handlers after table is rendered
        this.attachHeaderClickHandlers();
    }

    getStatusColor(status) {
        const colors = {
            'Active': 'bg-green-100 text-green-800',
            'Inactive': 'bg-gray-100 text-gray-800',
            'Terminated': 'bg-red-100 text-red-800',
            'On Leave': 'bg-yellow-100 text-yellow-800',
            'Probation': 'bg-blue-100 text-blue-800',
            'Resignation Pending': 'bg-orange-100 text-orange-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }

    renderPagination(data) {
        const controls = document.getElementById('paginationControls');
        if (!controls) return;

        this.totalPages = data.total_pages;
        const currentPage = data.page;

        let html = '';

        // Previous button
        if (currentPage > 1) {
            html += `
                <button onclick="employeeDirectory.goToPage(${currentPage - 1})" 
                        class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                    <iconify-icon icon="solar:alt-arrow-left-bold"></iconify-icon>
                </button>
            `;
        }

        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(this.totalPages, currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === currentPage;
            html += `
                <button onclick="employeeDirectory.goToPage(${i})" 
                        class="px-3 py-2 text-sm font-medium ${isActive 
                            ? 'text-white bg-primary border-primary' 
                            : 'text-gray-500 bg-white border-gray-300 hover:bg-gray-50'} border rounded-md">
                    ${i}
                </button>
            `;
        }

        // Next button
        if (currentPage < this.totalPages) {
            html += `
                <button onclick="employeeDirectory.goToPage(${currentPage + 1})" 
                        class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                    <iconify-icon icon="solar:alt-arrow-right-bold"></iconify-icon>
                </button>
            `;
        }

        controls.innerHTML = html;
    }

    updateRecordCount(data) {
        const recordCount = document.getElementById('recordCount');
        const paginationInfo = document.getElementById('paginationInfo');
        
        if (recordCount) {
            recordCount.textContent = `Showing ${data.employees.length} of ${data.total_count} employees`;
        }

        if (paginationInfo) {
            const start = ((data.page - 1) * data.limit) + 1;
            const end = Math.min(start + data.employees.length - 1, data.total_count);
            paginationInfo.textContent = `Showing ${start} to ${end} of ${data.total_count} results`;
        }
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadEmployees();
    }

    changePageSize() {
        this.pageSize = parseInt(document.getElementById('pageSize')?.value) || 50;
        this.currentPage = 1;
        this.loadEmployees();
    }

    toggleEmployeeSelect(employeeId) {
        if (this.selectedEmployees.has(employeeId)) {
            this.selectedEmployees.delete(employeeId);
        } else {
            this.selectedEmployees.add(employeeId);
        }

        this.updateSelectAllState();
        this.updateBulkActionsVisibility();
    }

    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.employee-checkbox');
        const selectAll = document.getElementById('selectAll')?.checked;

        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll;
            const employeeId = parseInt(checkbox.value);
            if (selectAll) {
                this.selectedEmployees.add(employeeId);
            } else {
                this.selectedEmployees.delete(employeeId);
            }
        });

        this.updateBulkActionsVisibility();
    }

    updateSelectAllState() {
        const checkboxes = document.querySelectorAll('.employee-checkbox');
        const selectAll = document.getElementById('selectAll');
        
        if (selectAll && checkboxes.length > 0) {
            const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
            selectAll.checked = checkedCount === checkboxes.length;
            selectAll.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
        }
    }

    updateBulkActionsVisibility() {
        // Add bulk actions UI if needed
        if (this.selectedEmployees.size > 0) {
            // Show bulk actions
            console.log(`${this.selectedEmployees.size} employees selected`);
        }
    }

    async editEmployee(employeeId) {
        try {
            const response = await fetch(`/api/employees/${employeeId}`);
            if (!response.ok) throw new Error('Failed to fetch employee');
            
            const employee = await response.json();
            this.editingEmployee = employee;
            this.showEmployeeModal(employee);
            
        } catch (error) {
            console.error('Error loading employee:', error);
            this.showToast('Error loading employee details', 'error');
        }
    }

    viewEmployee(employeeId) {
        // Implement view functionality
        console.log('View employee:', employeeId);
    }

    async deleteEmployee(employeeId) {
        if (!confirm('Are you sure you want to delete this employee? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/employees/${employeeId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to delete employee');
            
            this.showToast('Employee deleted successfully', 'success');
            this.loadEmployees();
            this.loadEmployeeStatistics();
            
        } catch (error) {
            console.error('Error deleting employee:', error);
            this.showToast('Error deleting employee', 'error');
        }
    }

    showEmployeeModal(employee = null) {
        const modal = document.getElementById('employeeModal');
        const title = document.getElementById('modalTitle');
        const form = document.getElementById('employeeForm');
        const passwordField = document.getElementById('passwordField');
        
        if (!modal) return;

        // Reset form
        form.reset();
        
        if (employee) {
            title.textContent = 'Edit Employee';
            passwordField.style.display = 'none';
            
            // Populate form
            document.getElementById('employeeNo').value = employee.employee_no || '';
            document.getElementById('fullName').value = employee.full_name || '';
            document.getElementById('email').value = employee.email || '';
            document.getElementById('roleName').value = employee.role_name || '';
            document.getElementById('department').value = employee.department || '';
            document.getElementById('campaign').value = employee.campaign || '';
            document.getElementById('phoneNo').value = employee.phone_no || '';
            document.getElementById('dateOfJoining').value = employee.date_of_joining || '';
            document.getElementById('personalEmail').value = employee.personal_email || '';
            document.getElementById('clientEmail').value = employee.client_email || '';
            document.getElementById('employeeStatus').value = employee.employee_status || 'Active';
        } else {
            title.textContent = 'Add New Employee';
            passwordField.style.display = 'block';
            this.editingEmployee = null;
        }
        
        modal.classList.remove('hidden');
    }

    closeEmployeeModal() {
        document.getElementById('employeeModal')?.classList.add('hidden');
        this.editingEmployee = null;
    }

    async saveEmployee() {
        const form = document.getElementById('employeeForm');
        const formData = new FormData(form);

        // Collect form data
        const data = {
            employee_no: document.getElementById('employeeNo').value,
            full_name: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            role_name: document.getElementById('roleName').value,
            department: document.getElementById('department').value,
            campaign: document.getElementById('campaign').value,
            phone_no: document.getElementById('phoneNo').value,
            date_of_joining: document.getElementById('dateOfJoining').value,
            personal_email: document.getElementById('personalEmail').value,
            client_email: document.getElementById('clientEmail').value,
            employee_status: document.getElementById('employeeStatus').value
        };

        try {
            let response;
            
            if (this.editingEmployee) {
                // Update existing employee
                response = await fetch(`/api/employees/${this.editingEmployee.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } else {
                // Create new employee
                const formDataToSend = new FormData();
                Object.keys(data).forEach(key => {
                    if (data[key]) formDataToSend.append(key, data[key]);
                });
                formDataToSend.append('password', document.getElementById('password').value);
                
                response = await fetch('/api/employees', {
                    method: 'POST',
                    body: formDataToSend
                });
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save employee');
            }

            const result = await response.json();
            this.showToast(result.message || 'Employee saved successfully', 'success');
            this.closeEmployeeModal();
            this.loadEmployees();
            this.loadEmployeeStatistics();

        } catch (error) {
            console.error('Error saving employee:', error);
            this.showToast(error.message || 'Error saving employee', 'error');
        }
    }

    resetFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('departmentFilter').value = '';
        document.getElementById('campaignFilter').value = '';
        document.getElementById('statusFilter').value = '';
        this.currentPage = 1;
        this.loadEmployees();
        this.loadEmployeeStatistics();
        this.updateActiveFilterCount();
    }

    applyFilters() {
        this.currentPage = 1;
        this.loadEmployees();
        this.updateFilteredStatistics();
        this.updateActiveFilterCount();
    }

    updateActiveFilterCount() {
        const department = document.getElementById('departmentFilter')?.value || '';
        const campaign = document.getElementById('campaignFilter')?.value || '';
        const status = document.getElementById('statusFilter')?.value || '';
        const search = document.getElementById('searchInput')?.value || '';
        
        let activeCount = 0;
        if (department) activeCount++;
        if (campaign) activeCount++;
        if (status) activeCount++;
        if (search) activeCount++;
        
        const badge = document.getElementById('activeFilterCount');
        if (badge) {
            badge.textContent = activeCount;
        }
    }

    showToast(message, type = 'info') {
        // Simple toast implementation
        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        
        toast.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-transform duration-300`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.transform = 'translateY(-100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Export functions
    exportEmployees() {
        // Implement CSV/Excel export
        console.log('Export employees');
        this.showToast('Export functionality will be implemented', 'info');
    }

    importEmployees() {
        // Implement import functionality
        console.log('Import employees');
        this.showToast('Import functionality will be implemented', 'info');
    }

    // Bulk actions
    showBulkActionsModal() {
        if (this.selectedEmployees.size === 0) {
            this.showToast('Please select employees first', 'warning');
            return;
        }
        document.getElementById('bulkActionsModal')?.classList.remove('hidden');
    }

    closeBulkActionsModal() {
        document.getElementById('bulkActionsModal')?.classList.add('hidden');
    }

    async bulkStatusUpdate(status) {
        if (this.selectedEmployees.size === 0) return;

        try {
            const response = await fetch('/api/employees/bulk-status-update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    employee_ids: Array.from(this.selectedEmployees),
                    status: status
                })
            });

            if (!response.ok) throw new Error('Failed to update employee status');

            const result = await response.json();
            this.showToast(result.message, 'success');
            this.closeBulkActionsModal();
            this.selectedEmployees.clear();
            this.loadEmployees();

        } catch (error) {
            console.error('Error updating employee status:', error);
            this.showToast('Error updating employee status', 'error');
        }
    }

    async openEmployeeDrawer(employeeId) {
        try {
            const response = await fetch(`/api/employees/${employeeId}`);
            if (!response.ok) throw new Error('Failed to load employee');
            
            const employee = await response.json();
            this.renderEmployeeDrawer(employee);
            
            // Show drawer and overlay
            const drawer = document.getElementById('employeeDrawer');
            const overlay = document.getElementById('drawerOverlay');
            if (drawer && overlay) {
                overlay.classList.remove('hidden');
                drawer.classList.remove('translate-x-full');
            }
        } catch (error) {
            console.error('Error loading employee details:', error);
            this.showToast('Error loading employee details', 'error');
        }
    }

    closeEmployeeDrawer() {
        const drawer = document.getElementById('employeeDrawer');
        const overlay = document.getElementById('drawerOverlay');
        if (drawer && overlay) {
            drawer.classList.add('translate-x-full');
            overlay.classList.add('hidden');
        }
    }

    renderEmployeeDrawer(employee) {
        const content = document.getElementById('employeeDrawerContent');
        if (!content) return;

        const statusColor = this.getStatusColor(employee.employee_status);
        
        content.innerHTML = `
            <!-- Employee Header -->
            <div class="mb-6 pb-6 border-b border-gray-200">
                <div class="flex items-center gap-4 mb-4">
                    <div class="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                        <span class="text-2xl font-bold text-primary">${employee.full_name.charAt(0)}</span>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-gray-900">${employee.full_name}</h3>
                        <p class="text-sm text-gray-600">${employee.employee_no}</p>
                    </div>
                </div>
                <span class="inline-flex px-3 py-1 text-xs font-semibold rounded-full ${statusColor}">
                    ${employee.employee_status}
                </span>
            </div>

            <!-- Employee Info Section -->
            <div class="space-y-6">
                <!-- Contact Information -->
                <div>
                    <h4 class="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">Contact Information</h4>
                    <div class="space-y-2">
                        <div>
                            <p class="text-xs text-gray-600">Work Email</p>
                            <p class="text-sm font-medium text-gray-900">${employee.email || '-'}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-600">Personal Email</p>
                            <p class="text-sm font-medium text-gray-900">${employee.personal_email || '-'}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-600">Phone Number</p>
                            <p class="text-sm font-medium text-gray-900">${employee.phone_no || '-'}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-600">Client Email</p>
                            <p class="text-sm font-medium text-gray-900">${employee.client_email || '-'}</p>
                        </div>
                    </div>
                </div>

                <!-- Employment Information -->
                <div>
                    <h4 class="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">Employment Information</h4>
                    <div class="space-y-2">
                        <div>
                            <p class="text-xs text-gray-600">Campaign</p>
                            <p class="text-sm font-medium text-gray-900">${employee.campaign || '-'}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-600">Department</p>
                            <p class="text-sm font-medium text-gray-900">${employee.department || '-'}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-600">Date of Joining</p>
                            <p class="text-sm font-medium text-gray-900">${employee.date_of_joining ? this.formatDate(employee.date_of_joining) : '-'}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-600">Last Working Date</p>
                            <p class="text-sm font-medium text-gray-900">${employee.last_working_date ? this.formatDate(employee.last_working_date) : '-'}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-600">Tenure</p>
                            <p class="text-sm font-medium text-gray-900">${employee.tenure_months ? employee.tenure_months + ' months' : '-'}</p>
                        </div>
                    </div>
                </div>

                <!-- Additional Information -->
                <div>
                    <h4 class="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">Additional Information</h4>
                    <div class="space-y-2">
                        <div>
                            <p class="text-xs text-gray-600">Assessment Due Date</p>
                            <p class="text-sm font-medium text-gray-900">${employee.assessment_due_date ? this.formatDate(employee.assessment_due_date) : '-'}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-600">Regularization Date</p>
                            <p class="text-sm font-medium text-gray-900">${employee.regularization_date ? this.formatDate(employee.regularization_date) : '-'}</p>
                        </div>
                    </div>
                </div>

                <!-- Actions -->
                <div class="pt-4 border-t border-gray-200 space-y-2">
                    <button onclick="employeeDirectory.editEmployee(${employee.id})" 
                            class="w-full px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2">
                        <iconify-icon icon="solar:pen-bold"></iconify-icon>
                        Edit Employee
                    </button>
                    <button onclick="employeeDirectory.deleteEmployee(${employee.id})" 
                            class="w-full px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors flex items-center justify-center gap-2">
                        <iconify-icon icon="solar:trash-bin-minimalistic-bold"></iconify-icon>
                        Delete Employee
                    </button>
                </div>
            </div>
        `;
    }
}

// Initialize the employee directory when the page loads
let employeeDirectory;
document.addEventListener('DOMContentLoaded', () => {
    employeeDirectory = new EmployeeDirectory();
    
    // Restore filters panel state on page load
    const filtersPanelOpen = localStorage.getItem('filtersPanelOpen') !== 'false';
    if (filtersPanelOpen) {
        const panel = document.getElementById('filtersPanel');
        const btn = document.getElementById('filterToggleBtn');
        if (panel) {
            panel.classList.remove('hidden');
            btn.classList.add('ring-2', 'ring-primary/30');
        }
    }
});

// Global functions for HTML onclick handlers
function showAddEmployeeModal() {
    employeeDirectory.showEmployeeModal(null);
}

function closeEmployeeModal() {
    employeeDirectory.closeEmployeeModal();
}

function resetFilters() {
    employeeDirectory.resetFilters();
}

function applyFilters() {
    employeeDirectory.applyFilters();
}

function changePageSize() {
    employeeDirectory.changePageSize();
}

function exportEmployees() {
    employeeDirectory.exportEmployees();
}

function importEmployees() {
    employeeDirectory.importEmployees();
}

function toggleSelectAll() {
    employeeDirectory.toggleSelectAll();
}

function showBulkActionsModal() {
    employeeDirectory.showBulkActionsModal();
}

function closeBulkActionsModal() {
    employeeDirectory.closeBulkActionsModal();
}

function bulkStatusUpdate(status) {
    employeeDirectory.bulkStatusUpdate(status);
}

function toggleFiltersPanel() {
    const panel = document.getElementById('filtersPanel');
    const btn = document.getElementById('filterToggleBtn');
    if (panel) {
        panel.classList.toggle('hidden');
        btn.classList.toggle('ring-2');
        btn.classList.toggle('ring-primary/30');
        // Save preference to localStorage
        localStorage.setItem('filtersPanelOpen', !panel.classList.contains('hidden'));
    }
}