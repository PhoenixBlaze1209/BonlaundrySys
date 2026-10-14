
// Mock globals
let elementStore = {};
function getEl(id) {
    if (!elementStore[id]) {
        elementStore[id] = {
            id,
            classList: { toggle: () => {}, add: () => {}, remove: () => {}, contains: () => false },
            setAttribute: () => {},
            appendChild: () => {},
            style: {},
            textContent: '',
            innerHTML: '',
            querySelector: () => ({ value: 'Paid' }),
            querySelectorAll: () => [],
            addEventListener: () => {}
        };
    }
    return elementStore[id];
}
const window = { closeSidebar: () => {} };
const document = {
    getElementById: getEl,
    createElement: (tag) => getEl(tag),
    body: getEl('body'),
    querySelectorAll: () => [],
    addEventListener: () => {}
};
const Chart = function() { return { data: { labels: [], datasets: [{}] }, update: () => {} }; };
const fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'success', data: { metrics: {}, activities: [], forecast: { chart_data: [1,2], chart_labels: ['A','B'] } } }) });
const setInterval = () => {};
const setTimeout = () => {};
const requestAnimationFrame = () => {};




        const currentRole = '""';
        const isManager = currentRole === 'Manager';
        const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
        let predictiveChart;

        // TOAST NOTIFICATIONS (No AI Slop / No native alert popups)
        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            const bgClass = type === 'success' ? 'bg-emerald-800 text-white border-emerald-700' :
                            type === 'error' ? 'bg-rose-800 text-white border-rose-700' :
                            'bg-slate-900 text-white border-slate-800';
            
            toast.className = `${bgClass} pointer-events-auto p-4 rounded-xl shadow-lg border text-xs font-semibold flex items-center justify-between gap-3 transition-all transform duration-300 translate-y-2 opacity-0`;
            toast.innerHTML = `
                <span>${message}</span>
                <button onclick="this.parentElement.remove()" class="text-white/70 hover:text-white font-bold text-sm">&times;</button>
            `;
            container.appendChild(toast);
            requestAnimationFrame(() => {
                toast.classList.remove('translate-y-2', 'opacity-0');
            });
            setTimeout(() => {
                toast.classList.add('opacity-0', 'translate-y-2');
                setTimeout(() => toast.remove(), 300);
            }, 4500);
        }

        // UNIVERSAL CRUD CONFIRMATION MODAL WITH EXPLICIT CONSEQUENCE MESSAGING
        function showConfirmModal({ 
            title = 'Confirm Action', 
            message = 'Are you sure you want to proceed?', 
            consequence = 'This action will update the system and cannot be undone.',
            confirmText = 'Confirm', 
            type = 'default',
            onConfirm 
        }) {
            const modal = document.getElementById('confirm-modal');
            const titleEl = document.getElementById('confirm-modal-title');
            const descEl = document.getElementById('confirm-modal-desc');
            const consequenceEl = document.getElementById('confirm-modal-consequence-text');
            const consequenceBox = document.getElementById('confirm-modal-consequence-box');
            const iconContainer = document.getElementById('confirm-modal-icon-container');
            const confirmBtn = document.getElementById('confirm-modal-confirm-btn');
            const confirmLabel = document.getElementById('confirm-modal-confirm-label');
            const cancelBtn = document.getElementById('confirm-modal-cancel-btn');
            
            if (!modal) {
                if (confirm(`${message}\n\nConsequence: ${consequence}`)) onConfirm();
                return;
            }

            titleEl.textContent = title;
            descEl.textContent = message;
            consequenceEl.textContent = consequence;
            confirmLabel.textContent = confirmText;

            // Type theme styling
            if (type === 'danger') {
                iconContainer.className = 'w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center flex-shrink-0';
                consequenceBox.className = 'p-3.5 bg-rose-50/70 border border-rose-200 rounded-xl text-xs space-y-1';
                confirmBtn.className = 'px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition shadow-sm flex items-center gap-1.5';
            } else if (type === 'warning') {
                iconContainer.className = 'w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0';
                consequenceBox.className = 'p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl text-xs space-y-1';
                confirmBtn.className = 'px-4 py-2 text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 rounded-xl transition shadow-sm flex items-center gap-1.5';
            } else {
                iconContainer.className = 'w-10 h-10 rounded-xl bg-sky-50 text-[#0284C7] flex items-center justify-center flex-shrink-0';
                consequenceBox.className = 'p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs space-y-1';
                confirmBtn.className = 'px-4 py-2 text-xs font-bold text-white bg-[#0284C7] hover:bg-[#0369A1] rounded-xl transition shadow-sm flex items-center gap-1.5';
            }

            modal.classList.remove('hidden');

            const cleanUp = () => {
                modal.classList.add('hidden');
                confirmBtn.disabled = false;
                confirmBtn.onclick = null;
                cancelBtn.onclick = null;
            };

            confirmBtn.onclick = async () => {
                confirmBtn.disabled = true;
                confirmLabel.textContent = 'Processing...';
                try {
                    await onConfirm();
                } catch (err) {
                    showToast(err.message || 'Action failed', 'error');
                } finally {
                    cleanUp();
                }
            };
            cancelBtn.onclick = cleanUp;
        }

        // SKELETON HELPERS
        function getTableSkeletonHtml(cols = 6, rows = 3) {
            return Array.from({length: rows}).map(() => `
                <tr>
                    ${Array.from({length: cols}).map((_, i) => `
                        <td class="py-3.5 px-3">
                            <div class="skeleton-text ${i === 0 ? 'w-28' : i === cols - 1 ? 'w-20 ml-auto' : 'w-20'}"></div>
                        </td>
                    `).join('')}
                </tr>
            `).join('');
        }

        // GENERIC SAFE API CALLER
        async function api(url, options) {
            const response = await fetch(url, options);
            const payload = await response.json();
            if (!response.ok || payload.status === 'error') {
                throw new Error(payload.message || 'Request failed.');
            }
            return payload;
        }

        // LIVE DASHBOARD METRICS FETCH
        function fetchRealtimeData() {
            fetch('/api/dashboard/summary')
                .then(res => res.ok ? res.json() : Promise.reject(res.status))
                .then(response => {
                    const { metrics, activities, forecast } = response.data;
                    const elActive = document.getElementById('metric-active-queue');
                    if (elActive) elActive.textContent = metrics.active_queue ?? 0;
                    const elWait = document.getElementById('metric-wait-time');
                    if (elWait) elWait.textContent = `${metrics.est_wait_time_mins ?? 0} mins`;
                    const elMach = document.getElementById('metric-machines');
                    if (elMach) elMach.textContent = `${metrics.machines_ready ?? 0} / ${metrics.total_machines ?? 0}`;
                    const elRev = document.getElementById('metric-revenue');
                    if (isManager && elRev && metrics.today_revenue_php != null) {
                        elRev.textContent = `₱${Number(metrics.today_revenue_php).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
                    }
                    renderActivities(activities || []);
                    if (forecast) {
                        const maxFootfall = Math.max(...(forecast.chart_data || [0]));
                        const totalDayForecast = (forecast.chart_data || []).reduce((a, b) => a + b, 0) || 1;
                        const peakIntensityPercent = Math.min(100, Math.round((maxFootfall / totalDayForecast) * 100 * 3.5));
                        const elPeak = document.getElementById('forecast-peak');
                        if (elPeak) elPeak.textContent = forecast.predicted_peak;
                        const elLoad = document.getElementById('forecast-load-label');
                        if (elLoad) elLoad.textContent = `${Math.round(maxFootfall)} Checkouts/hr`;
                        const elBar = document.getElementById('forecast-load-bar');
                        if (elBar) elBar.style.width = `${peakIntensityPercent}%`;
                        const elHeroTitle = document.getElementById('live-hero-title');
                        if (elHeroTitle) elHeroTitle.textContent = `${forecast.predicted_peak} Expected Peak`;
                        const elHeroDesc = document.getElementById('live-hero-desc');
                        if (elHeroDesc) elHeroDesc.textContent = forecast.insight;
                        const elMape = document.getElementById('analytics-mape');
                        if (elMape) elMape.textContent = forecast.mape === null ? 'Gathering data' : `${forecast.mape.toFixed(1)}%`;
                        if (predictiveChart) {
                            predictiveChart.data.labels = forecast.chart_labels;
                            if (forecast.historical_data) {
                                predictiveChart.data.datasets[0].data = forecast.historical_data;
                            }
                            predictiveChart.data.datasets[1].data = forecast.chart_data;
                            predictiveChart.update();
                        }
                    }
                })
                .catch(err => console.error('Dashboard sync error:', err));
        }

        function renderActivities(activities) {
            const list = document.getElementById('live-activity-list');
            if (!list) return;
            if (!activities.length) {
                list.innerHTML = '<p class="text-xs text-slate-400 py-6 text-center">No active machine queue entries right now.</p>';
                return;
            }
            list.innerHTML = activities.map(act => {
                const isGraveyard = (act.priority_level || '').includes('Graveyard') || (act.turnaround_option || '').includes('2 Day');
                const isExpress = (act.priority_level || '').includes('Express') || (act.turnaround_option || '').includes('24');
                const badgeHtml = isGraveyard 
                    ? `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">🌙 Graveyard Batch</span>`
                    : (isExpress ? `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-sky-50 text-[#0284C7] border border-sky-200">⚡ 24h Express</span>`
                                 : `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-slate-100 text-slate-600">Standard</span>`);
                
                const payStatus = act.payment_status || 'Paid';
                const isPaid = payStatus.toLowerCase() === 'paid';
                const payBadge = `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full ${isPaid ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-200'}">${isPaid ? '✓ Paid' : '⏳ Pending'}</span>`;

                return `
                <div onclick="${act.appointment_id ? `openOrderDetailsModalById(${act.appointment_id})` : ''}" class="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-100 rounded-2xl hover:border-[#0284C7] hover:bg-white hover:shadow-xs transition ${act.appointment_id ? 'cursor-pointer' : ''}">
                    <div class="flex items-center gap-3">
                        <span class="text-xs font-bold text-[#0284C7] font-mono-num bg-sky-50 px-2 py-0.5 rounded-lg border border-sky-100">${act.job_id}</span>
                        <div>
                            <div class="flex items-center gap-1.5 flex-wrap">
                                <span class="text-xs font-bold text-slate-800">${esc(act.customer)}</span>
                                ${badgeHtml}
                                ${payBadge}
                            </div>
                            <span class="text-[11px] text-slate-400 block mt-0.5">${esc(act.machine || 'Assigned machine')}</span>
                        </div>
                    </div>
                    <span class="px-2.5 py-1 text-[10px] font-bold text-sky-700 bg-sky-50 border border-sky-200 rounded-full uppercase">${esc(act.status)}</span>
                </div>
            `}).join('');
        }

        // POS HELPERS & VALIDATION
        function setPOSWeight(val) {
            const weightInput = document.getElementById('pos-weight');
            if (weightInput) {
                weightInput.value = val;
                updatePOSPreview(false);
            }
        }

        function updatePOSPreview(syncCapacity = false) {
            const serviceSelect = document.getElementById('pos-service');
            if (!serviceSelect) return;
            const selectedOption = serviceSelect.selectedOptions[0];
            const basePrice = Number(selectedOption.dataset.price || 0);
            
            const addonCheckboxes = Array.from(document.querySelectorAll('input[name="pos_addons"]:checked'));
            const addonPrices = {
                'superwash_self': 105,
                'fold': 40,
                'sort': 30,
                'add_dry': 70,
                'delivery': 100
            };
            const addonsTotal = addonCheckboxes.reduce((sum, cb) => sum + (addonPrices[cb.value] || 0), 0);
            const total = basePrice + addonsTotal;

            document.getElementById('pos-total').textContent = `₱${total.toFixed(2)}`;
            document.getElementById('pos-receipt-service-label').textContent = selectedOption.textContent.split(' — ')[0];
            document.getElementById('pos-receipt-service-price').textContent = `₱${basePrice.toFixed(2)}`;

            const weightInput = document.getElementById('pos-weight');
            const capacity = serviceSelect.value === 'self_13' ? 13 : 8;
            weightInput.max = capacity;
            if (syncCapacity || !weightInput.value || Number(weightInput.value) > capacity) {
                weightInput.value = capacity;
            }
            document.getElementById('pos-weight-summary').textContent = `${weightInput.value} kg`;

            const addonsContainer = document.getElementById('pos-receipt-addons-container');
            if (addonsContainer) {
                addonsContainer.innerHTML = addonCheckboxes.length ? addonCheckboxes.map(cb => `
                    <div class="flex justify-between text-slate-600">
                        <span>+ ${cb.nextElementSibling.textContent.split(' (')[0]}</span>
                        <span class="font-mono-num">+₱${(addonPrices[cb.value] || 0).toFixed(2)}</span>
                    </div>
                `).join('') : '<span class="text-[11px] text-slate-400">No add-ons selected</span>';
            }

            loadMachines();
        }

        function checkoutPOS() {
            // Error prevention & validation
            const nameInput = document.getElementById('pos-customer-name');
            const emailInput = document.getElementById('pos-customer-email');
            const weightInput = document.getElementById('pos-weight');
            const errName = document.getElementById('pos-err-name');
            const errEmail = document.getElementById('pos-err-email');
            const errWeight = document.getElementById('pos-err-weight');

            let hasError = false;
            if (errName) errName.classList.add('hidden');
            if (errEmail) errEmail.classList.add('hidden');
            if (errWeight) errWeight.classList.add('hidden');

            const customer_name = nameInput.value.trim();
            if (!customer_name) {
                if (errName) errName.classList.remove('hidden');
                nameInput.focus();
                hasError = true;
            }

            const customer_email = emailInput.value.trim();
            if (customer_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(customer_email)) {
                if (errEmail) errEmail.classList.remove('hidden');
                if (!hasError) emailInput.focus();
                hasError = true;
            }

            const weight = Number(weightInput.value || 0);
            if (weight <= 0 || weight > Number(weightInput.max || 13)) {
                if (errWeight) errWeight.classList.remove('hidden');
                if (!hasError) weightInput.focus();
                hasError = true;
            }

            const machineSelect = document.getElementById('pos-machine');
            const machine_id = machineSelect.value;
            if (!machine_id) {
                showToast('No compatible machine is selected.', 'error');
                hasError = true;
            }

            if (hasError) return;

            const machineName = machineSelect.selectedOptions[0]?.textContent || 'Selected Machine';
            const payment_status = document.querySelector('input[name="pos_payment"]:checked')?.value || 'Paid';
            const serviceSelect = document.getElementById('pos-service');
            const service_code = serviceSelect.value;
            const serviceLabel = serviceSelect.selectedOptions[0].textContent.split(' — ')[0];
            const addons = Array.from(document.querySelectorAll('input[name="pos_addons"]:checked')).map(cb => cb.value);
            const cycle_type = document.getElementById('pos-cycle-type').value;
            const totalDue = document.getElementById('pos-total').textContent;

            // Trigger Confirmation Modal with explicit consequence messaging
            showConfirmModal({
                title: 'Confirm Counter Checkout & Start Load',
                message: `Start ${serviceLabel} for customer "${customer_name}" (${weight} kg) on ${machineName}?`,
                consequence: `This will lock ${machineName} for a ${cycle_type} cycle, generate a transaction receipt for ${totalDue} (${payment_status}), and add the customer to the active queue.`,
                confirmText: 'Charge & Start Load',
                type: 'default',
                onConfirm: async () => {
                    const result = await api('/pos/checkout', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            weight, customer_email, customer_name, payment_status,
                            service_code, addons, machine_id, cycle_type
                        })
                    });
                    const sale = result.data;
                    showToast(`Sale recorded (TRX-${String(sale.transaction_id).padStart(4, '0')})! Machine started/queued.`, 'success');
                    nameInput.value = '';
                    emailInput.value = '';
                    document.querySelectorAll('input[name="pos_addons"]').forEach(cb => cb.checked = false);
                    updatePOSPreview(false);
                    fetchRealtimeData();
                    loadQueue();
                    loadMachines();
                }
            });
        }

        // LOAD MACHINES & RENDER STATUS GRID (WITH SKELETON LOADERS)
        async function loadMachines() {
            try {
                const result = await api('/api/machines');
                const machines = result.data;
                const posSelect = document.getElementById('pos-machine');
                
                if (posSelect) {
                    const previous = posSelect.value;
                    const required = Number(document.getElementById('pos-weight')?.value || 0);
                    const compatible = machines
                        .filter(m => !['maintenance', 'not_available'].includes(m.status) && m.capacity_kg >= required)
                        .sort((a, b) => {
                            const aFree = a.status === 'available', bFree = b.status === 'available';
                            if (aFree !== bFree) return aFree ? -1 : 1;
                            if (!aFree && a.queue_count !== b.queue_count) return a.queue_count - b.queue_count;
                            if (!aFree && a.remaining_minutes !== b.remaining_minutes) return a.remaining_minutes - b.remaining_minutes;
                            return a.usage_count - b.usage_count;
                        });

                    posSelect.innerHTML = compatible.map((m, i) => {
                        const statusLabel = m.status === 'available' ? 'Ready Now' : `${m.remaining_minutes}m left (${m.queue_count} queued)`;
                        return `<option value="${m.machine_id}">${i === 0 ? '★ Recommended: ' : ''}${m.name} (${m.capacity_kg}kg • ${statusLabel})</option>`;
                    }).join('') || '<option value="">No compatible machines available</option>';

                    if (compatible.some(m => String(m.machine_id) === previous)) posSelect.value = previous;
                }

                // Grid view for Machine Status tab
                const grid = document.getElementById('machine-status-grid');
                if (grid) {
                    grid.innerHTML = machines.map(m => {
                        const isAvailable = m.status === 'available';
                        const isMaint = m.status === 'maintenance' || m.status === 'not_available';
                        const borderClass = isAvailable ? 'border-emerald-200 bg-emerald-50/40' :
                                            isMaint ? 'border-rose-200 bg-rose-50/40' : 'border-sky-200 bg-sky-50/40';
                        const pillClass = isAvailable ? 'bg-emerald-100 text-emerald-800' :
                                          isMaint ? 'bg-rose-100 text-rose-800' : 'bg-sky-100 text-sky-800';
                        
                        const queuedDetails = m.queued_customers.length
                            ? `<div class="mt-3 pt-2.5 border-t border-slate-200/60 text-[11px]">
                                <span class="font-bold text-slate-700 block mb-1">In Line:</span>
                                ${m.queued_customers.map(c => `<span class="text-slate-600 block">#${c.queue_number} ${c.customer_name}</span>`).join('')}
                               </div>`
                            : '<p class="text-[10px] text-slate-400 mt-2.5">No queued customers waiting</p>';

                        return `
                            <div class="app-card p-4 border ${borderClass} flex flex-col justify-between">
                                <div>
                                    <div class="flex justify-between items-center mb-2">
                                        <h5 class="font-bold text-sm text-slate-900">${m.name}</h5>
                                        <span class="px-2 py-0.5 text-[9px] font-bold rounded-full uppercase ${pillClass}">${m.status}</span>
                                    </div>
                                    <p class="text-xs text-slate-600">${m.capacity_kg}kg Capacity • ₱${m.price_per_cycle}/cycle</p>
                                    <p class="text-xs text-slate-800 font-semibold mt-1">Current: ${m.customer_name || 'Idle'}</p>
                                    ${m.remaining_minutes ? `
                                        <div class="mt-2 space-y-1">
                                            <div class="flex justify-between text-[10px] font-mono-num text-slate-600 font-bold">
                                                <span>Time remaining:</span>
                                                <span class="text-[#0284C7]">${m.remaining_minutes} mins</span>
                                            </div>
                                            <div class="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                                <div class="h-full bg-[#0284C7] rounded-full" style="width: ${Math.max(10, 100 - (m.remaining_minutes * 2.5))}%"></div>
                                            </div>
                                        </div>
                                    ` : ''}
                                </div>
                                ${queuedDetails}
                            </div>
                        `;
                    }).join('');
                }

                // Settings list for manager
                const settingsList = document.getElementById('machine-settings-list');
                if (settingsList) {
                    settingsList.innerHTML = machines.map(m => `
                        <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 items-center text-xs border border-slate-200 p-2.5 rounded-xl bg-white">
                            <input id="machine-name-${m.machine_id}" value="${m.name}" class="border border-slate-200 p-2 rounded-lg text-xs font-semibold">
                            <input id="machine-price-${m.machine_id}" type="number" value="${m.price_per_cycle}" class="border border-slate-200 p-2 rounded-lg text-xs font-mono-num">
                            <select id="machine-state-${m.machine_id}" class="border border-slate-200 p-2 rounded-lg text-xs font-medium bg-white">
                                <option value="available" ${m.status === 'available' ? 'selected' : ''}>Operational (Available)</option>
                                <option value="maintenance" ${m.status === 'maintenance' ? 'selected' : ''}>Maintenance</option>
                                <option value="not_available" ${m.status === 'not_available' ? 'selected' : ''}>Offline / Out of Order</option>
                            </select>
                            <button onclick="saveMachine(${m.machine_id})" class="bg-slate-900 hover:bg-slate-800 text-white font-bold p-2 rounded-lg text-xs transition">Save Changes</button>
                        </div>
                    `).join('');
                }
            } catch (err) {
                console.error('Machine fetch error:', err);
            }
        }

        function saveMachine(id) {
            const name = document.getElementById(`machine-name-${id}`).value;
            const price = document.getElementById(`machine-price-${id}`).value;
            const state = document.getElementById(`machine-state-${id}`).value;

            showConfirmModal({
                title: 'Update Machine Configuration',
                message: `Save changes for ${name} (₱${price}/cycle • Status: ${state})?`,
                consequence: state === 'maintenance' || state === 'not_available' 
                    ? `⚠️ Taking this machine offline will immediately prevent it from accepting POS and online appointment loads.`
                    : `Updating pricing will apply to all subsequent counter checkout calculations.`,
                confirmText: 'Save Configuration',
                type: state === 'maintenance' ? 'warning' : 'default',
                onConfirm: async () => {
                    await api(`/api/machines/${id}`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            machine_name: name,
                            price_per_cycle: price,
                            operational_state: state
                        })
                    });
                    showToast('Machine settings updated successfully.', 'success');
                    loadMachines();
                }
            });
        }

        // QUEUE MANAGEMENT (WITH PAYMENT BADGE & INSPECTION TRIGGER)
        async function loadQueue() {
            const table = document.getElementById('queue-table-body');
            if (!table) return;
            try {
                const [queueResult, summary] = await Promise.all([api('/api/queue'), api('/api/dashboard/summary')]);
                const items = queueResult.data || [];
                if (!items.length) {
                    table.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-400">The customer queue is currently clear.</td></tr>';
                    return;
                }
                table.innerHTML = items.map(item => {
                    const payMethod = item.payment_method || 'Cash';
                    const payStatus = item.payment_status || 'Pending';
                    const isPaid = payStatus.toLowerCase() === 'paid';
                    const isCash = payMethod.toLowerCase().includes('cash');
                    const payIcon = payMethod.includes('GCash') || payMethod.includes('E-Wallet') ? '📱' : (payMethod.includes('Bank') ? '🏦' : '💵');

                    const paymentToggle = (currentRole !== 'Customer' && isCash && item.appointment_id) ? `
                        <button onclick="event.stopPropagation(); toggleOrderPaidStatus(${item.appointment_id}, '${payStatus}')" class="px-2 py-0.5 text-[9px] font-extrabold rounded-full ${isPaid ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-300'} hover:opacity-80 transition" title="Toggle Payment Status">
                            ${payIcon} ${esc(payStatus)}
                        </button>
                    ` : `
                        <span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full ${isPaid ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-300'}">
                            ${payIcon} ${esc(payStatus)}
                        </span>
                    `;

                    return `
                    <tr onclick="${item.appointment_id ? `openOrderDetailsModalById(${item.appointment_id})` : ''}" class="hover:bg-slate-50/80 cursor-pointer transition">
                        <td class="py-3 px-3">
                            <span class="bg-slate-100 text-slate-700 font-bold px-2 py-1 rounded-md text-[11px] font-mono-num">#${item.queue_number}</span>
                        </td>
                        <td class="py-3 px-3">
                            <div class="font-bold text-slate-900">${esc(item.customer)}</div>
                            <span class="text-[10px] text-slate-400 font-mono-num">${esc(item.order_code || 'ORD')}</span>
                        </td>
                        <td class="py-3 px-3 text-slate-600">${esc(item.service_type)}</td>
                        <td class="py-3 px-3 text-[#0284C7] font-bold">${esc(item.machine)}</td>
                        <td class="py-3 px-3">
                            ${paymentToggle}
                        </td>
                        <td class="py-3 px-3">
                            <span class="px-2.5 py-0.5 text-[10px] font-bold rounded-full ${item.status === 'Processing' ? 'bg-sky-50 text-[#0284C7]' : 'bg-amber-50 text-amber-700'} uppercase">
                                ${esc(item.status)} ${item.status === 'Waiting' ? `(~${item.estimated_waiting_time}m)` : ''}
                            </span>
                        </td>
                        <td class="py-3 px-3 text-right" onclick="event.stopPropagation()">
                            ${currentRole !== 'Customer' ? `
                                <button onclick="advanceQueue(${item.queue_id}, '${esc(item.customer)}', '${esc(item.status)}')" class="px-3 py-1 bg-[#0284C7] hover:bg-[#0369A1] text-white font-bold rounded-lg text-xs transition shadow-sm">
                                    Advance Stage →
                                </button>
                            ` : ''}
                        </td>
                    </tr>
                `}).join('');
            } catch (err) {
                console.error('Queue load error:', err);
                table.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-400 text-xs font-semibold">Unable to load queue at the moment. <button onclick="loadQueue()" class="text-[#0284C7] underline font-bold ml-1">Retry</button></td></tr>';
            }
        }

        function addWalkInQueue() {
            showConfirmModal({
                title: 'Add Walk-in Customer to Queue',
                message: 'Issue a new sequential queue ticket for a walk-in customer?',
                consequence: 'This allocates the next queue number and recalculates estimated wait times for all waiting visitors.',
                confirmText: 'Generate Ticket',
                type: 'default',
                onConfirm: async () => {
                    const result = await api('/api/queue', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
                    showToast(`Walk-in customer added as Queue #${result.data.queue_number}`, 'success');
                    await Promise.all([loadQueue(), fetchRealtimeData()]);
                }
            });
        }

        function advanceQueue(id, customerName, currentStatus) {
            const isWaiting = currentStatus === 'Waiting';
            showConfirmModal({
                title: isWaiting ? 'Start Machine for Waiting Customer' : 'Complete & Free Machine',
                message: isWaiting 
                    ? `Advance Queue entry for ${customerName} to in-progress processing?`
                    : `Mark laundry cycle for ${customerName} as finished and free the machine?`,
                consequence: isWaiting 
                    ? 'This locks the assigned washer/dryer and starts the countdown timer.'
                    : 'This marks the queue ticket as Done, clears the machine, and dispatches the next waiting load.',
                confirmText: isWaiting ? 'Start Machine' : 'Complete Cycle',
                type: 'default',
                onConfirm: async () => {
                    const res = await api(`/api/queue/${id}/advance`, {method: 'POST'});
                    showToast(res.message, 'success');
                    await Promise.all([loadQueue(), loadMachines(), fetchRealtimeData()]);
                }
            });
        }

        // APPOINTMENTS & ORDER LOBBY WORKFLOW (WITH SKELETON LOADERS, FILTERS & MODAL INSPECTION)
        let currentApptTab = 'active';
        let loadedAppointmentsData = [];
        let currentLobbyFilter = 'all';
        let currentModalOrder = null;

        function switchAppointmentTab(tab) {
            currentApptTab = tab;
            const btnActive = document.getElementById('btn-appt-active');
            const btnCompleted = document.getElementById('btn-appt-completed');
            const btnCancelled = document.getElementById('btn-appt-cancelled');
            
            const activeClass = 'px-3.5 py-1.5 text-xs font-bold rounded-lg transition bg-white text-slate-900 shadow-sm flex items-center gap-1.5';
            const inactiveClass = 'px-3.5 py-1.5 text-xs font-semibold text-slate-500 rounded-lg transition hover:text-slate-900 flex items-center gap-1.5';

            if (btnActive) btnActive.className = tab === 'active' ? activeClass : inactiveClass;
            if (btnCompleted) btnCompleted.className = tab === 'completed' ? activeClass : inactiveClass;
            if (btnCancelled) btnCancelled.className = tab === 'cancelled' ? activeClass.replace(' flex items-center gap-1.5', '') : inactiveClass.replace(' flex items-center gap-1.5', '');

            // Skeleton placeholder
            const list = document.getElementById('appointment-list');
            if (list) {
                list.innerHTML = `
                    <div class="bg-white border border-slate-200/80 rounded-xl p-5 space-y-3">
                        <div class="flex justify-between items-center">
                            <div class="skeleton-text w-32"></div>
                            <div class="skeleton h-6 w-24"></div>
                        </div>
                        <div class="skeleton-text w-64"></div>
                    </div>
                `;
            }

            loadAppointments(tab);
        }

        function setLobbyFilter(filterKey, element) {
            currentLobbyFilter = filterKey;
            document.querySelectorAll('.lobby-filter-btn').forEach(btn => {
                btn.className = 'lobby-filter-btn px-3 py-1 rounded-lg font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] transition';
            });
            if (element) {
                element.className = 'lobby-filter-btn px-3 py-1 rounded-lg font-bold bg-[#0284C7] text-white text-[11px] transition shadow-sm';
            }
            renderFilteredAppointments();
        }

        function filterAppointmentCards() {
            renderFilteredAppointments();
        }

        function renderFilteredAppointments() {
            const list = document.getElementById('appointment-list');
            if (!list) return;
            const searchVal = (document.getElementById('appt-search-input')?.value || '').trim().toLowerCase();

            const items = loadedAppointmentsData.filter(item => {
                // Lobby filter logic
                if (currentLobbyFilter === 'pickup') {
                    const isPickup = (item.order_mode || '').toLowerCase().includes('pick') || (item.service_type || '').toLowerCase().includes('pick');
                    if (!isPickup) return false;
                } else if (currentLobbyFilter === 'dropoff') {
                    const isPickup = (item.order_mode || '').toLowerCase().includes('pick') || (item.service_type || '').toLowerCase().includes('pick');
                    if (isPickup) return false;
                } else if (currentLobbyFilter === 'unpaid') {
                    if ((item.payment_status || '').toLowerCase() === 'paid') return false;
                } else if (currentLobbyFilter === 'transit') {
                    const fulfill = (item.fulfillment_status || '').toLowerCase();
                    if (!fulfill.includes('delivery') && !fulfill.includes('ready')) return false;
                }

                // Search query filter
                if (searchVal) {
                    const matchId = (item.order_code || '').toLowerCase().includes(searchVal);
                    const matchName = (item.customer || '').toLowerCase().includes(searchVal);
                    const matchPhone = (item.phone_number || '').toLowerCase().includes(searchVal);
                    const matchService = (item.service_type || '').toLowerCase().includes(searchVal);
                    const matchFulfill = (item.fulfillment_status || '').toLowerCase().includes(searchVal);
                    if (!matchId && !matchName && !matchPhone && !matchService && !matchFulfill) return false;
                }

                return true;
            });

            if (!items.length) {
                list.innerHTML = `<div class="bg-slate-50 rounded-2xl p-8 text-center text-slate-400 text-xs font-medium border border-slate-200/60">No orders match the current filter or search query.</div>`;
                return;
            }

            list.innerHTML = items.map(item => {
                const sched = item.schedule_time ? new Date(item.schedule_time) : null;
                const formattedDate = (sched && !isNaN(sched)) ? sched.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Flexible';
                const formattedTime = (sched && !isNaN(sched)) ? sched.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : '';

                const isGraveyard = (item.priority_level || '').includes('Graveyard') || (item.turnaround_option || '').includes('2 Day');
                const isExpress = (item.priority_level || '').includes('Express') || (item.turnaround_option || '').includes('24');
                const priorityBadge = isGraveyard
                    ? `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">🌙 Graveyard Batch (2-Day)</span>`
                    : (isExpress ? `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-sky-50 text-[#0284C7] border border-sky-200">⚡ 24h Express</span>`
                                 : `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-slate-100 text-slate-700">Standard</span>`);

                const payMethod = item.payment_method || 'Cash';
                const payStatus = item.payment_status || 'Pending';
                const isPaid = payStatus.toLowerCase() === 'paid';
                const isCash = payMethod.toLowerCase().includes('cash');
                const payIcon = payMethod.includes('GCash') || payMethod.includes('E-Wallet') ? '📱' : (payMethod.includes('Bank') ? '🏦' : '💵');

                const fulfill = item.fulfillment_status || 'Waiting Drop-off';
                const isPickupDelivery = (item.order_mode || '').includes('Pick') || (item.service_type || '').includes('Pick');

                // Quick fulfillment action button depending on status & mode
                let fulfillmentActionBtn = '';
                if (currentRole !== 'Customer' && item.status !== 'Completed' && item.status !== 'Cancelled') {
                    if (isPickupDelivery) {
                        if (fulfill === 'For Pickup') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); updateOrderFulfillment(${item.appointment_id}, 'Picked Up')" class="px-3 py-1.5 bg-[#0284C7] hover:bg-[#0369A1] text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1">
                                    <span>Pick Up by Staff ➔</span>
                                </button>
                            `;
                        } else if (fulfill === 'Picked Up' || fulfill === 'In Laundry' || item.status === 'Confirmed') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); updateOrderFulfillment(${item.appointment_id}, 'Out for Delivery')" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1">
                                    <span>Out for Delivery 🚀</span>
                                </button>
                            `;
                        } else if (fulfill === 'Out for Delivery') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); updateOrderFulfillment(${item.appointment_id}, 'Delivered')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1">
                                    <span>Mark Delivered ✓</span>
                                </button>
                            `;
                        }
                    } else {
                        if (item.status === 'Pending' || fulfill === 'Waiting Drop-off') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); checkInAppointment(${item.appointment_id}, '${esc(item.customer)}')" class="px-3 py-1.5 bg-[#0284C7] hover:bg-[#0369A1] text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1">
                                    <span>Accept & Start ➔</span>
                                </button>
                            `;
                        } else if (fulfill === 'In Laundry' || item.status === 'Confirmed') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); updateOrderFulfillment(${item.appointment_id}, 'Ready for Pick-up')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1">
                                    <span>Ready for Pick-up ➔</span>
                                </button>
                            `;
                        } else if (fulfill === 'Ready for Pick-up') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); completeAppointment(${item.appointment_id}, '${esc(item.customer)}')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1">
                                    <span>Customer Picked Up ✓</span>
                                </button>
                            `;
                        }
                    }
                }

                // Payment toggle button
                let paymentToggleBtn = '';
                if (currentRole !== 'Customer' && isCash) {
                    if (isPaid) {
                        paymentToggleBtn = `
                            <button onclick="event.stopPropagation(); toggleOrderPaidStatus(${item.appointment_id}, 'Paid')" title="Click to revert to Pending" class="px-2 py-0.5 text-[9px] font-bold text-slate-500 hover:text-amber-700 bg-slate-100 hover:bg-amber-50 rounded-lg transition">
                                Revert
                            </button>
                        `;
                    } else {
                        paymentToggleBtn = `
                            <button onclick="event.stopPropagation(); toggleOrderPaidStatus(${item.appointment_id}, 'Pending')" class="px-2.5 py-1 text-[10px] font-black text-emerald-800 bg-emerald-100 hover:bg-emerald-200 border border-emerald-300 rounded-lg transition shadow-xs flex items-center gap-1">
                                <span>💵 Mark Paid</span>
                            </button>
                        `;
                    }
                }

                return `
                    <div onclick="openOrderDetailsModalById(${item.appointment_id})" class="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:border-[#0284C7] hover:shadow-md cursor-pointer transition">
                        <div class="flex items-start gap-3.5 flex-1 min-w-0">
                            <div class="w-11 h-11 rounded-2xl ${item.status === 'Completed' ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-sky-50 text-[#0284C7] border border-sky-200'} flex flex-col items-center justify-center font-bold text-xs flex-shrink-0">
                                <span class="text-[9px] font-mono leading-none text-slate-400">TKT</span>
                                <span class="font-mono-num font-black">${item.queue_number ? `#${item.queue_number}` : 'ORD'}</span>
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2 flex-wrap">
                                    <h4 class="text-sm font-extrabold text-slate-900 truncate">${esc(item.customer)}</h4>
                                    <span class="text-[10px] font-mono-num text-slate-500 bg-slate-100 px-2 py-0.5 rounded font-bold">${esc(item.order_code)}</span>
                                    ${priorityBadge}
                                    <span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full ${isPaid ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-300'}">
                                        ${payIcon} ${esc(payMethod)} • ${esc(payStatus)}
                                    </span>
                                </div>
                                <p class="text-xs text-slate-600 mt-1 flex items-center flex-wrap gap-1.5">
                                    <span class="font-bold text-slate-800">${esc(item.service_type)}</span>
                                    <span class="text-slate-300">•</span>
                                    <span>${formattedDate} at ${formattedTime}</span>
                                    ${item.pickup_time ? `<span class="text-slate-300">•</span><span class="text-slate-500 font-medium">Slot: ${esc(item.pickup_time)}</span>` : ''}
                                </p>
                                <div class="flex items-center gap-3 text-[11px] text-slate-500 mt-1 flex-wrap">
                                    <span class="text-sky-700 font-bold bg-sky-50 px-2 py-0.2 rounded">${esc(fulfill)}</span>
                                    ${item.phone_number ? `<span class="font-mono-num text-slate-600">📞 ${esc(item.phone_number)}</span>` : ''}
                                    ${item.address && item.address !== '—' ? `<span class="text-slate-600 truncate max-w-[200px]">📍 ${esc(item.address)}</span>` : ''}
                                </div>
                            </div>
                        </div>

                        <!-- Action Controls Area -->
                        <div class="flex items-center gap-2.5 self-end sm:self-center flex-shrink-0" onclick="event.stopPropagation()">
                            ${paymentToggleBtn}
                            ${fulfillmentActionBtn}
                            <button onclick="openOrderDetailsModalById(${item.appointment_id})" class="px-3 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold rounded-xl text-xs transition">
                                Inspect 🔍
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        async function loadAppointments(status = null) {
            const currentTab = status || currentApptTab;
            const list = document.getElementById('appointment-list');
            if (!list) return;
            try {
                const result = await api(`/api/appointments?status=${currentTab}`);
                loadedAppointmentsData = result.data || [];
                const counts = result.counts || { active: 0, completed: 0 };
                
                const countActive = document.getElementById('appt-count-active');
                const countCompleted = document.getElementById('appt-count-completed');
                if (countActive) countActive.textContent = counts.active;
                if (countCompleted) countCompleted.textContent = counts.completed;

                renderFilteredAppointments();
            } catch (err) {
                console.error('Appointments load error:', err);
                list.innerHTML = `<div class="bg-slate-50 text-slate-500 rounded-2xl p-6 text-center text-xs font-semibold border border-slate-200">Unable to load appointments. <button onclick="loadAppointments()" class="text-[#0284C7] underline font-bold ml-1">Retry</button></div>`;
            }
        }

        function openOrderDetailsModalById(appointmentId) {
            const found = loadedAppointmentsData.find(a => a.appointment_id === appointmentId);
            if (found) {
                openOrderDetailsModal(found);
            } else {
                // Fetch appointment directly if not in current view
                api('/api/appointments').then(res => {
                    const match = (res.data || []).find(a => a.appointment_id === appointmentId);
                    if (match) openOrderDetailsModal(match);
                });
            }
        }

        function openOrderDetailsModal(order) {
            currentModalOrder = order;
            const modal = document.getElementById('order-details-modal');
            if (!modal) return;

            document.getElementById('modal-order-id').textContent = order.order_code || `ORD-${order.appointment_id}`;
            document.getElementById('modal-order-created').textContent = `Scheduled: ${new Date(order.schedule_time).toLocaleString()}`;
            document.getElementById('modal-order-queue-badge').textContent = order.queue_number ? `Queue #${order.queue_number}` : 'Scheduled';
            document.getElementById('modal-customer-name').textContent = order.customer || 'Customer';
            document.getElementById('modal-customer-phone').textContent = order.phone_number || '—';
            document.getElementById('modal-customer-address').textContent = order.address || '—';
            document.getElementById('modal-service-type').textContent = order.service_type || 'Classic Wash, Dry, Fold';

            const isGraveyard = (order.priority_level || '').includes('Graveyard') || (order.turnaround_option || '').includes('2 Day');
            document.getElementById('modal-turnaround-sla').textContent = isGraveyard ? '🌙 2 Days Economy (Graveyard Batch)' : '⚡ 24 Hours Express';

            const payMethod = order.payment_method || 'Cash';
            const payStatus = order.payment_status || 'Pending';
            const isPaid = payStatus.toLowerCase() === 'paid';
            const isCash = payMethod.toLowerCase().includes('cash');
            const payIcon = payMethod.includes('GCash') || payMethod.includes('E-Wallet') ? '📱 ' : (payMethod.includes('Bank') ? '🏦 ' : '💵 ');

            document.getElementById('modal-payment-method').textContent = `${payIcon}${payMethod}`;
            const statusBadge = document.getElementById('modal-payment-status-badge');
            statusBadge.textContent = payStatus;
            statusBadge.className = isPaid 
                ? 'px-2.5 py-1 text-xs font-black rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 inline-block mt-0.5'
                : 'px-2.5 py-1 text-xs font-black rounded-full bg-amber-100 text-amber-800 border border-amber-300 inline-block mt-0.5';

            const toggleBtn = document.getElementById('modal-payment-toggle-btn');
            const hint = document.getElementById('modal-payment-hint');
            if (isPaid) {
                toggleBtn.textContent = 'Revert to Pending ↩';
                toggleBtn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold transition shadow-sm bg-slate-200 hover:bg-slate-300 text-slate-700';
                hint.textContent = 'Digital / Verified payment received.';
            } else {
                toggleBtn.textContent = 'Mark as Paid ✓';
                toggleBtn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold transition shadow-sm bg-emerald-600 hover:bg-emerald-700 text-white';
                hint.textContent = 'Collect cash upon counter drop-off or doorstep delivery.';
            }

            const fulfill = order.fulfillment_status || 'Waiting Drop-off';
            document.getElementById('modal-fulfillment-badge').textContent = fulfill;
            const selectEl = document.getElementById('modal-fulfillment-select');
            if (selectEl) {
                selectEl.value = fulfill;
            }

            // Action buttons
            const btnCheckIn = document.getElementById('modal-action-checkin');
            const btnComplete = document.getElementById('modal-action-complete');
            if (order.status === 'Pending') {
                btnCheckIn?.classList.remove('hidden');
                btnComplete?.classList.add('hidden');
            } else if (order.status === 'Confirmed') {
                btnCheckIn?.classList.add('hidden');
                btnComplete?.classList.remove('hidden');
            } else {
                btnCheckIn?.classList.add('hidden');
                btnComplete?.classList.add('hidden');
            }

            modal.classList.remove('hidden');
        }

        function closeOrderDetailsModal() {
            const modal = document.getElementById('order-details-modal');
            if (modal) modal.classList.add('hidden');
            currentModalOrder = null;
        }

        async function toggleOrderPaidStatus(appointmentId, currentStatus) {
            const newStatus = currentStatus === 'Paid' ? 'Pending' : 'Paid';
            try {
                const res = await api(`/api/appointments/${appointmentId}/payment-status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ payment_status: newStatus })
                });
                showToast(res.message, 'success');
                await Promise.all([loadAppointments(), loadQueue(), fetchRealtimeData()]);
                if (currentModalOrder && currentModalOrder.appointment_id === appointmentId) {
                    const updated = loadedAppointmentsData.find(a => a.appointment_id === appointmentId);
                    if (updated) openOrderDetailsModal(updated);
                }
            } catch (err) {
                showToast(err.message, 'error');
            }
        }

        async function toggleModalPaymentStatus() {
            if (!currentModalOrder) return;
            await toggleOrderPaidStatus(currentModalOrder.appointment_id, currentModalOrder.payment_status);
        }

        async function updateOrderFulfillment(appointmentId, stage) {
            try {
                const res = await api(`/api/appointments/${appointmentId}/fulfillment-status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ fulfillment_status: stage })
                });
                showToast(res.message || `Fulfillment stage advanced to "${stage}"`, 'success');
                await Promise.all([loadAppointments(), loadQueue(), fetchRealtimeData()]);
                if (currentModalOrder && currentModalOrder.appointment_id === appointmentId) {
                    const updated = loadedAppointmentsData.find(a => a.appointment_id === appointmentId);
                    if (updated) openOrderDetailsModal(updated);
                }
            } catch (err) {
                showToast(err.message, 'error');
            }
        }

        async function updateModalFulfillmentStatus() {
            if (!currentModalOrder) return;
            const stage = document.getElementById('modal-fulfillment-select').value;
            await updateOrderFulfillment(currentModalOrder.appointment_id, stage);
        }

        function checkInFromModal() {
            if (!currentModalOrder) return;
            const order = currentModalOrder;
            closeOrderDetailsModal();
            checkInAppointment(order.appointment_id, order.customer);
        }

        function completeFromModal() {
            if (!currentModalOrder) return;
            const order = currentModalOrder;
            closeOrderDetailsModal();
            completeAppointment(order.appointment_id, order.customer);
        }

        function checkInAppointment(id, customerName) {
            showConfirmModal({
                title: 'Accept & Check-in Garments',
                message: `Accept drop-off garments from "${customerName}" and start machine cycle?`,
                consequence: 'This confirms garment intake, changes status to In-Progress, and reserves the next available washer.',
                confirmText: 'Accept & Start Washer',
                type: 'default',
                onConfirm: async () => {
                    const res = await api(`/api/appointments/${id}/check-in`, {method: 'POST'});
                    showToast(res.message, 'success');
                    await Promise.all([loadAppointments(), fetchRealtimeData(), loadQueue(), loadMachines()]);
                }
            });
        }

        function completeAppointment(id, customerName) {
            showConfirmModal({
                title: 'Mark Order as Picked Up & Fulfilled',
                message: `Confirm that freshly laundered garments were handed over to "${customerName}"?`,
                consequence: 'This marks the order as Completed, releases any remaining machine locks, and archives the record.',
                confirmText: 'Mark Picked Up',
                type: 'default',
                onConfirm: async () => {
                    const res = await api(`/api/appointments/${id}/complete`, {method: 'POST'});
                    showToast(res.message, 'success');
                    await Promise.all([loadAppointments(), fetchRealtimeData(), loadQueue(), loadMachines()]);
                }
            });
        }

        function cancelAppointment(id, customerName) {
            showConfirmModal({
                title: 'Cancel Scheduled Appointment',
                message: `Are you sure you want to cancel the appointment for "${customerName}"?`,
                consequence: '⚠️ This permanently frees the scheduled machine slot and removes the reservation from the daily calendar.',
                confirmText: 'Yes, Cancel Appointment',
                type: 'danger',
                onConfirm: async () => {
                    const res = await api(`/api/appointments/${id}/cancel`, {method: 'POST'});
                    showToast(res.message, 'info');
                    await Promise.all([loadAppointments(), fetchRealtimeData(), loadQueue()]);
                }
            });
        }

        // SALES & RECONCILIATION TALLY
        let currentSalesPage = 1;
        let currentSalesLimit = 15;
        let currentSalesDateFilter = null;
        let currentSalesStatusFilter = 'all';

        function switchSalesSubTab(tab) {
            const dailySec = document.getElementById('sales-sub-daily-section');
            const ledgerSec = document.getElementById('sales-sub-ledger-section');
            const btnDaily = document.getElementById('btn-sales-sub-daily');
            const btnLedger = document.getElementById('btn-sales-sub-ledger');
            if (!dailySec || !ledgerSec) return;
            if (tab === 'daily') {
                dailySec.classList.remove('hidden');
                ledgerSec.classList.add('hidden');
                btnDaily.className = 'px-4 py-1.5 text-xs font-bold rounded-lg transition bg-white text-slate-900 shadow-sm';
                btnLedger.className = 'px-4 py-1.5 text-xs font-semibold text-slate-500 rounded-lg transition hover:text-slate-900';
                loadSalesTally();
            } else {
                dailySec.classList.add('hidden');
                ledgerSec.classList.remove('hidden');
                btnLedger.className = 'px-4 py-1.5 text-xs font-bold rounded-lg transition bg-white text-slate-900 shadow-sm';
                btnDaily.className = 'px-4 py-1.5 text-xs font-semibold text-slate-500 rounded-lg transition hover:text-slate-900';
                loadSales();
            }
        }

        async function loadSalesTally(days = null) {
            const limitDays = days !== null ? days : (document.getElementById('sales-daily-limit')?.value || 7);
            const tableBody = document.getElementById('sales-daily-table-body');
            if (!tableBody) return;
            tableBody.innerHTML = getTableSkeletonHtml(8, 3);
            try {
                const response = await api(`/api/manager/sales-tally?limit_days=${limitDays}`);
                const { data, metrics } = response;
                
                if (metrics) {
                    const elToday = document.getElementById('sales-kpi-today');
                    const elTodaySub = document.getElementById('sales-kpi-today-sub');
                    const elWeek = document.getElementById('sales-kpi-week');
                    const elMonth = document.getElementById('sales-kpi-month');
                    const elAll = document.getElementById('sales-kpi-all');
                    const elAllSub = document.getElementById('sales-kpi-all-sub');
                    if (elToday) elToday.textContent = `₱${metrics.today_gross.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                    if (elTodaySub) elTodaySub.textContent = `${metrics.today_count} checkouts • ${metrics.today_weight} kg`;
                    if (elWeek) elWeek.textContent = `₱${metrics.week_gross.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                    if (elMonth) elMonth.textContent = `₱${metrics.month_gross.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                    if (elAll) elAll.textContent = `₱${metrics.all_time_gross.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                    if (elAllSub) elAllSub.textContent = `${metrics.all_time_count} total orders (${metrics.all_time_weight} kg)`;
                }

                if (!data || !data.length) {
                    tableBody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-slate-400">No daily sales tallies recorded yet.</td></tr>';
                    return;
                }

                tableBody.innerHTML = data.map(day => `
                    <tr class="hover:bg-slate-50/60 transition">
                        <td class="py-3 px-3">
                            <div class="font-bold text-slate-900">${day.display_date}</div>
                            <span class="text-[10px] text-slate-400">${day.day_name}</span>
                        </td>
                        <td class="py-3 px-3">
                            <span class="font-bold text-slate-800 font-mono-num">${day.tx_count}</span>
                            <span class="text-[10px] text-slate-400">orders</span>
                        </td>
                        <td class="py-3 px-3 text-slate-700 font-medium font-mono-num">${day.total_weight_kg} kg</td>
                        <td class="py-3 px-3 font-bold text-emerald-600 font-mono-num">₱${day.paid_sales.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td class="py-3 px-3 ${day.unpaid_sales > 0 ? 'text-amber-600 font-bold' : 'text-slate-400'} font-mono-num">₱${day.unpaid_sales.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td class="py-3 px-3 font-black text-[#0284C7] font-mono-num">₱${day.gross_sales.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td class="py-3 px-3">
                            <span class="px-2.5 py-0.5 text-[9px] font-bold rounded-full ${day.unpaid_sales === 0 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'} uppercase">
                                ${day.tally_status}
                            </span>
                        </td>
                        <td class="py-3 px-3 text-right">
                            <button onclick="drillDownSalesDay('${day.date}', '${day.display_date}')" class="px-3 py-1 bg-slate-100 hover:bg-[#0284C7] hover:text-white rounded-lg text-xs font-bold text-slate-700 transition">
                                View Receipts →
                            </button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        function drillDownSalesDay(dateStr, displayDate) {
            currentSalesDateFilter = dateStr;
            currentSalesPage = 1;
            const badge = document.getElementById('sales-active-filter-badge');
            const label = document.getElementById('sales-filter-date-label');
            if (badge && label) {
                label.textContent = displayDate;
                badge.classList.remove('hidden');
                badge.classList.add('flex');
            }
            switchSalesSubTab('ledger');
        }

        function clearSalesDateFilter() {
            currentSalesDateFilter = null;
            currentSalesPage = 1;
            const badge = document.getElementById('sales-active-filter-badge');
            if (badge) {
                badge.classList.add('hidden');
                badge.classList.remove('flex');
            }
            loadSales();
        }

        function changeSalesLimit(newLimit) {
            currentSalesLimit = newLimit;
            currentSalesPage = 1;
            loadSales();
        }

        function filterSalesStatus(newStatus) {
            currentSalesStatusFilter = newStatus;
            currentSalesPage = 1;
            loadSales();
        }

        function changeSalesPage(delta) {
            currentSalesPage += delta;
            loadSales();
        }

        async function loadSales() {
            const tableBody = document.getElementById('sales-table-body');
            if (!tableBody) return;
            tableBody.innerHTML = getTableSkeletonHtml(6, 4);
            try {
                let url = `/api/transactions?page=${currentSalesPage}&limit=${currentSalesLimit}`;
                if (currentSalesDateFilter) url += `&date=${encodeURIComponent(currentSalesDateFilter)}`;
                if (currentSalesStatusFilter && currentSalesStatusFilter !== 'all') url += `&status=${encodeURIComponent(currentSalesStatusFilter)}`;
                
                const result = await api(url);
                const sales = result.data || [];
                const pag = result.pagination || { total_records: sales.length, page: 1, limit: currentSalesLimit, total_pages: 1, has_prev: false, has_next: false };
                
                const info = document.getElementById('sales-pagination-info');
                const indicator = document.getElementById('sales-page-indicator');
                const btnPrev = document.getElementById('sales-btn-prev');
                const btnNext = document.getElementById('sales-btn-next');
                
                const startRecord = pag.total_records === 0 ? 0 : (pag.page - 1) * pag.limit + 1;
                const endRecord = Math.min(pag.page * pag.limit, pag.total_records);
                
                if (info) info.textContent = `Showing ${startRecord}–${endRecord} of ${pag.total_records} receipts`;
                if (indicator) indicator.textContent = `Page ${pag.page} of ${pag.total_pages}`;
                if (btnPrev) btnPrev.disabled = !pag.has_prev;
                if (btnNext) btnNext.disabled = !pag.has_next;
                
                if (!sales.length) {
                    tableBody.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">No matching transaction receipts found.</td></tr>';
                    return;
                }
                
                tableBody.innerHTML = sales.map(sale => `
                    <tr class="hover:bg-slate-50/60 transition">
                        <td class="py-3 px-3 text-slate-500 font-mono-num text-[11px]">${sale.created_at ? new Date(sale.created_at).toLocaleString() : '--'}</td>
                        <td class="py-3 px-3 text-slate-800 font-bold font-mono-num text-xs">TRX-${String(sale.transaction_id).padStart(4, '0')}</td>
                        <td class="py-3 px-3 font-bold text-slate-900">${sale.customer}</td>
                        <td class="py-3 px-3 text-slate-600 font-medium capitalize font-mono-num">${sale.weight_kg}kg • ${sale.cycle_type || 'Wash'}</td>
                        <td class="py-3 px-3">
                            <span class="px-2.5 py-0.5 text-[9px] font-bold rounded-full ${sale.payment_status === 'Paid' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'} uppercase">
                                ${sale.payment_status || 'Paid'}
                            </span>
                        </td>
                        <td class="py-3 px-3 text-right text-[#0284C7] font-bold font-mono-num text-xs">
                            ₱${sale.total_amount.toLocaleString('en-US', {minimumFractionDigits: 2})}
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        // FREQUENT RESIDENT AUTO-SLOTTING
        async function loadGhostSlots(minVisits = null) {
            const tableBody = document.getElementById('ghost-slots-table-body');
            const dashBody = document.getElementById('ghost-slots-dash-body');
            const countBadge = document.getElementById('analytics-active-allocations');
            if (!tableBody && !dashBody) return;
            const threshold = minVisits !== null ? minVisits : (document.getElementById('modal-habit-threshold')?.value || 3);
            try {
                const response = await api(`/api/manager/ghost-slots?min_visits=${threshold}`);
                const slots = response.data || [];
                if (countBadge) countBadge.textContent = `${slots.length} Discovered`;
                
                const emptyRow = '<tr><td colspan="6" class="py-6 text-center text-slate-400">No recurring resident habits detected yet with the current threshold.</td></tr>';
                const rowsHtml = slots.length ? slots.map(slot => `
                    <tr class="hover:bg-slate-50/60 transition">
                        <td class="py-3 px-3">
                            <div class="font-bold text-slate-900">${slot.customer_name}</div>
                            <span class="text-[10px] text-slate-400">${slot.customer_email || 'Condo Resident'}</span>
                        </td>
                        <td class="py-3 px-3 text-slate-700">
                            <span class="font-bold text-[#0284C7] font-mono-num">${slot.usual_time}</span>
                        </td>
                        <td class="py-3 px-3">
                            <span class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-slate-100 text-slate-600 font-mono-num">${slot.total_visits} checkouts</span>
                        </td>
                        <td class="py-3 px-3">
                            <span class="capitalize font-mono-num">${slot.avg_weight}kg • ${slot.preferred_cycle}</span>
                        </td>
                        <td class="py-3 px-3">
                            <div class="font-bold ${slot.recommended_wait_mins === 0 ? 'text-emerald-600' : 'text-amber-600'} flex items-center gap-1.5">
                                <span class="w-1.5 h-1.5 rounded-full ${slot.recommended_wait_mins === 0 ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
                                <span>${slot.recommendation_text}</span>
                            </div>
                        </td>
                        <td class="py-3 px-3 text-right">
                            <button onclick="assignGhostSlot('${slot.customer_name}', ${slot.avg_weight}, '${slot.preferred_cycle}', '${slot.customer_email || ''}')" class="bg-[#0284C7] hover:bg-[#0369A1] text-white font-bold px-3 py-1.5 rounded-xl text-[10px] transition shadow-sm">
                                Assign Machine →
                            </button>
                        </td>
                    </tr>
                `).join('') : emptyRow;

                if (tableBody) tableBody.innerHTML = rowsHtml;
                if (dashBody) dashBody.innerHTML = rowsHtml;
            } catch (err) {
                console.error(err);
            }
        }

        function assignGhostSlot(name, weight, cycle, email) {
            showConfirmModal({
                title: 'Assign Regular Resident Slot',
                message: `Assign ${name} to the optimal lowest-queue machine for their regular ${weight}kg ${cycle} load?`,
                consequence: 'This dispatches the customer directly to the next free washer with 0 or minimal queue wait.',
                confirmText: 'Assign Machine',
                type: 'default',
                onConfirm: async () => {
                    const result = await api('/api/manager/ghost-slots/assign', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            customer_name: name,
                            weight_kg: weight,
                            cycle_type: cycle,
                            customer_email: email
                        })
                    });
                    showToast(result.message, 'success');
                    await Promise.all([loadGhostSlots(), fetchRealtimeData(), loadMachines(), loadQueue()]);
                }
            });
        }

        function toggleMatrixModal(show) {
            const modal = document.getElementById('matrix-settings-modal');
            if (modal) {
                if (show) modal.classList.remove('hidden');
                else modal.classList.add('hidden');
            }
        }

        function saveMatrixSettings() {
            const bufferMins = document.getElementById('modal-buffer-select').value;
            const threshold = document.getElementById('modal-habit-threshold').value;
            document.getElementById('analytics-buffer-threshold').textContent = `${bufferMins} mins`;
            toggleMatrixModal(false);
            loadGhostSlots(parseInt(threshold));
            showToast('Reservation parameters updated.', 'success');
        }

        // ACCOUNT CREATION & FORM VALIDATION
        function createAccount(event) {
            event.preventDefault();
            const form = event.currentTarget;
            const name = form.name.value.trim();
            const email = form.email.value.trim();
            const password = form.password.value;
            const role = form.role.value;

            const errName = document.getElementById('acc-err-name');
            const errEmail = document.getElementById('acc-err-email');
            const errPass = document.getElementById('acc-err-pass');

            let hasError = false;
            if (errName) errName.classList.add('hidden');
            if (errEmail) errEmail.classList.add('hidden');
            if (errPass) errPass.classList.add('hidden');

            if (!name) {
                if (errName) errName.classList.remove('hidden');
                hasError = true;
            }
            if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                if (errEmail) errEmail.classList.remove('hidden');
                hasError = true;
            }
            if (!password || password.length < 6) {
                if (errPass) errPass.classList.remove('hidden');
                hasError = true;
            }

            if (hasError) return;

            showConfirmModal({
                title: 'Provision New User Account',
                message: `Create a new "${role}" account for ${name} (${email})?`,
                consequence: `This will store encrypted credentials in MySQL and grant ${role} privileges immediately.`,
                confirmText: 'Create Account',
                type: 'default',
                onConfirm: async () => {
                    const result = await api('/manager/accounts', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(Object.fromEntries(new FormData(form)))
                    });
                    showToast(`Account created for ${result.data.name}!`, 'success');
                    form.reset();
                }
            });
        }

        // TAB NAVIGATION ROUTING
        function switchTab(tabId) {
            const tabs = document.querySelectorAll('.tab-view');
            const buttons = document.querySelectorAll('aside button[id^="btn-"]');
            const pageTitle = document.getElementById('page-title');
            const pageSubtitle = document.getElementById('page-subtitle');

            tabs.forEach(tab => tab.classList.add('hidden'));
            buttons.forEach(btn => btn.classList.remove('active-tab'));

            const activeTab = document.getElementById(`view-${tabId}`);
            const activeBtn = document.getElementById(`btn-${tabId}`);
            
            if (activeTab) activeTab.classList.remove('hidden');
            if (activeBtn) activeBtn.classList.add('active-tab');

            const tabMeta = {
                'dashboard': ['Dashboard', 'Real-time shop operations & machine status'],
                'pos': ['POS Register', 'Front-counter intake, load pricing & machine assignment'],
                'sales': ['Sales History & Tally', 'Audited gross revenue, loss prevention & receipts ledger'],
                'appointment': ['Appointments Tracker', 'Customer scheduled drop-offs and order fulfillment'],
                'queue': ['Queue Order', 'Active customer queue order and stage advancement'],
                'machines': ['Machine Fleet Telemetry', 'Live cycle status, countdowns, and maintenance flags'],
                'analytics': ['Peak Hours & Demand Forecast', 'Hourly footfall distributions and frequent resident slotting'],
                'settings': ['System Settings', 'User accounts & machine pricing configurations']
            };

            if (pageTitle && tabMeta[tabId]) {
                pageTitle.textContent = tabMeta[tabId][0];
                if (pageSubtitle) pageSubtitle.textContent = tabMeta[tabId][1];
            }

            if (tabId === 'sales') { loadSalesTally(); loadSales(); }
            if (tabId === 'appointment') loadAppointments();
            if (tabId === 'queue') { loadQueue(); loadMachines(); }
            if (tabId === 'pos') updatePOSPreview(false);
            if (tabId === 'analytics') loadGhostSlots();
            if (tabId === 'machines') loadMachines();
            if (tabId === 'settings') loadMachines();
            closeSidebar();
        }

        // INITIALIZATION
        document.addEventListener('DOMContentLoaded', () => {
            const sidebar = document.getElementById('app-sidebar');
            const sidebarToggle = document.getElementById('sidebar-toggle');
            let sidebarScrim;

            function setSidebar(open) {
                sidebar.classList.toggle('is-open', open);
                sidebarToggle?.setAttribute('aria-expanded', String(open));
                if (open) {
                    sidebarScrim = document.createElement('div');
                    sidebarScrim.className = 'sidebar-scrim';
                    sidebarScrim.addEventListener('click', closeSidebar);
                    document.body.appendChild(sidebarScrim);
                } else if (sidebarScrim) {
                    sidebarScrim.remove();
                    sidebarScrim = null;
                }
            }
            window.closeSidebar = () => setSidebar(false);
            sidebarToggle?.addEventListener('click', () => setSidebar(!sidebar.classList.contains('is-open')));

            // Initialize Peak Chart
            const initialLabels = "";
            const initialHistorical = "";
            const initialPredicted = "";

            const ctx = document.getElementById('chart-predictive-footfall');
            if (ctx && typeof Chart !== 'undefined') {
                predictiveChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: initialLabels,
                        datasets: [
                            {
                                label: 'Historical Average',
                                data: initialHistorical,
                                borderColor: '#94A3B8',
                                borderWidth: 2,
                                borderDash: [4, 4],
                                fill: false,
                                tension: 0.35
                            },
                            {
                                label: "Today's Forecast",
                                data: initialPredicted,
                                borderColor: '#0284C7',
                                borderWidth: 2.5,
                                backgroundColor: 'rgba(2, 132, 199, 0.08)',
                                fill: true,
                                tension: 0.35
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top',
                                labels: {
                                    boxWidth: 12,
                                    boxHeight: 4,
                                    font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
                                    color: '#64748B'
                                }
                            },
                            tooltip: {
                                padding: 10,
                                backgroundColor: '#0F172A',
                                titleFont: { family: 'Plus Jakarta Sans', size: 11, weight: '700' },
                                bodyFont: { family: 'Plus Jakarta Sans', size: 11 },
                                cornerRadius: 8
                            }
                        },
                        scales: {
                            x: {
                                grid: { display: false },
                                ticks: { font: { family: 'Plus Jakarta Sans', size: 10, weight: '600' }, color: '#94A3B8' }
                            },
                            y: {
                                grid: { color: '#F1F5F9' },
                                ticks: { font: { family: 'Plus Jakarta Sans', size: 10, weight: '600' }, color: '#94A3B8' }
                            }
                        }
                    }
                });
            }

            fetchRealtimeData();
            setInterval(fetchRealtimeData, 30000);
            loadAppointments();
            setInterval(loadAppointments, 30000);
            loadQueue();
            setInterval(loadQueue, 30000);
            if (document.getElementById('pos-service')) updatePOSPreview(true);
            loadMachines();
            setInterval(loadMachines, 30000);
            loadGhostSlots();

            const accountForm = document.getElementById('account-form');
            if (accountForm) accountForm.addEventListener('submit', createAccount);
        });
    

// Test calling renderActivities
try {
    renderActivities([{
        job_id: 'Q-001',
        customer: 'John Doe',
        machine: 'Washer 1',
        status: 'Waiting',
        priority_level: 'Standard',
        turnaround_option: '24 Hours',
        payment_status: 'Paid',
        appointment_id: 123
    }]);
    console.log("renderActivities SUCCESS!");
} catch(e) {
    console.log("renderActivities FAILED:", e.message);
}

// Test calling renderFilteredAppointments
try {
    loadedAppointmentsData = [{
        appointment_id: 1,
        order_code: 'ORD-12345',
        customer: 'Alice',
        phone_number: '09123456789',
        service_type: 'Wash-Dry-Fold',
        status: 'Pending',
        priority_level: 'Standard',
        turnaround_option: '24 Hours',
        schedule_time: '2026-09-05T10:00:00'
    }];
    renderFilteredAppointments();
    console.log("renderFilteredAppointments SUCCESS!");
} catch(e) {
    console.log("renderFilteredAppointments FAILED:", e.message);
}
