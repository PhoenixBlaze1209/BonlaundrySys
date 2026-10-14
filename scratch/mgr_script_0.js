
        const currentRole = [];
        let predictiveChart = null;

        const esc = s => String(s || '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');

        // TOAST NOTIFICATIONS (NON-BLOCKING)
        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            const bgClass = type === 'success' ? 'bg-emerald-800 text-white border-emerald-700' :
                type === 'error' ? 'bg-rose-800 text-white border-rose-700' :
                    'bg-slate-900 text-white border-slate-800';
            toast.className = `${bgClass} pointer-events-auto p-4 rounded-xl shadow-lg border text-xs font-semibold flex items-center justify-between gap-3 transition-all transform duration-300 translate-y-2 opacity-0`;
            toast.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()" class="text-white/70 hover:text-white font-bold">&times;</button>`;
            container.appendChild(toast);
            requestAnimationFrame(() => toast.classList.remove('translate-y-2', 'opacity-0'));
            setTimeout(() => {
                toast.classList.add('opacity-0', 'translate-y-2');
                setTimeout(() => toast.remove(), 300);
            }, 4500);
        }

        // CONFIRMATION MODAL WITH EXPLICIT CONSEQUENCE MESSAGING
        function showConfirmModal({
            title = 'Confirm Action',
            message = 'Are you sure you want to proceed?',
            consequence = 'This action will update records and cannot be undone.',
            confirmText = 'Confirm',
            type = 'default', // 'default' | 'danger' | 'warning'
            onConfirm
        }) {
            const modal = document.getElementById('confirm-modal');
            const titleEl = document.getElementById('confirm-modal-title');
            const descEl = document.getElementById('confirm-modal-desc');
            const consEl = document.getElementById('confirm-modal-consequence-text');
            const consBox = document.getElementById('confirm-modal-consequence-box');
            const confirmBtn = document.getElementById('confirm-modal-confirm-btn');
            const cancelBtn = document.getElementById('confirm-modal-cancel-btn');
            const labelEl = document.getElementById('confirm-modal-confirm-label');
            const iconContainer = document.getElementById('confirm-modal-icon-container');

            if (!modal) return;

            if (titleEl) titleEl.textContent = title;
            if (descEl) descEl.textContent = message;
            if (consEl) consEl.textContent = consequence;
            if (labelEl) labelEl.textContent = confirmText;

            if (type === 'danger') {
                confirmBtn.className = 'px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition shadow-sm flex items-center gap-1.5';
                if (iconContainer) iconContainer.className = 'w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center flex-shrink-0';
                if (consBox) consBox.className = 'p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs space-y-1';
            } else if (type === 'warning') {
                confirmBtn.className = 'px-4 py-2 text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 rounded-xl transition shadow-sm flex items-center gap-1.5';
                if (iconContainer) iconContainer.className = 'w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0';
                if (consBox) consBox.className = 'p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-1';
            } else {
                confirmBtn.className = 'px-4 py-2 text-xs font-bold text-white bg-[#0284C7] hover:bg-[#0369A1] rounded-xl transition shadow-sm flex items-center gap-1.5';
                if (iconContainer) iconContainer.className = 'w-10 h-10 rounded-xl bg-sky-50 text-[#0284C7] flex items-center justify-center flex-shrink-0';
                if (consBox) consBox.className = 'p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs space-y-1';
            }

            modal.classList.remove('hidden');

            const handleConfirm = async () => {
                const origText = labelEl ? labelEl.textContent : 'Confirm';
                if (confirmBtn) {
                    confirmBtn.disabled = true;
                    confirmBtn.classList.add('opacity-75', 'cursor-not-allowed');
                }
                if (cancelBtn) cancelBtn.disabled = true;
                if (labelEl) labelEl.innerHTML = '<svg class="w-3.5 h-3.5 animate-spin inline mr-1.5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg> Processing...';

                try {
                    if (typeof onConfirm === 'function') {
                        await onConfirm();
                    }
                } catch (err) {
                    showToast(err.message || 'Action failed', 'error');
                } finally {
                    if (confirmBtn) {
                        confirmBtn.disabled = false;
                        confirmBtn.classList.remove('opacity-75', 'cursor-not-allowed');
                    }
                    if (cancelBtn) cancelBtn.disabled = false;
                    if (labelEl) labelEl.textContent = origText;
                    cleanup();
                }
            };

            const cleanup = () => {
                modal.classList.add('hidden');
                confirmBtn?.removeEventListener('click', handleConfirm);
                cancelBtn?.removeEventListener('click', cleanup);
            };

            confirmBtn?.addEventListener('click', handleConfirm);
            cancelBtn?.addEventListener('click', cleanup);
        }

        // UNIVERSAL SKELETON ROW GENERATOR
        function getTableSkeletonHtml(cols = 6, rows = 3) {
            let html = '';
            for (let r = 0; r < rows; r++) {
                html += '<tr>';
                for (let c = 0; c < cols; c++) {
                    const widthClass = c === 0 ? 'w-24' : (c === cols - 1 ? 'w-16 ml-auto' : 'w-20');
                    html += `<td class="py-3 px-3"><div class="skeleton-text ${widthClass}"></div></td>`;
                }
                html += '</tr>';
            }
            return html;
        }

        // UNIVERSAL API CALLER WITH ERROR HANDLING
        async function api(url, options = {}) {
            const res = await fetch(url, options);
            const data = await res.json();
            if (!res.ok) {
                const message = data.message || 'An unexpected error occurred.';
                throw new Error(message);
            }
            return data;
        }

        // REAL-TIME DASHBOARD DATA SYNCHRONIZATION
        function fetchRealtimeData() {
            api('/api/dashboard/summary')
                .then(result => {
                    const data = result.data || {};
                    const metrics = data.metrics || {};
                    const activities = data.activities || [];
                    const forecast = data.forecast;

                    const qEl = document.getElementById('metric-active-queue');
                    if (qEl) qEl.textContent = metrics.active_queue ?? 0;

                    const wEl = document.getElementById('metric-wait-time');
                    if (wEl) wEl.textContent = `${metrics.est_wait_time_mins ?? 0} mins`;

                    const mEl = document.getElementById('metric-machines');
                    if (mEl) mEl.textContent = `${metrics.machines_ready ?? 0} / ${metrics.total_machines ?? 0}`;

                    const rEl = document.getElementById('metric-revenue');
                    if (rEl && currentRole === 'Manager') {
                        const rev = metrics.today_revenue_php ?? metrics.todays_revenue ?? 0;
                        rEl.textContent = `₱${Number(rev).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
                    }

                    // Dynamic Sidebar Badges
                    const sbAppt = document.getElementById('sidebar-badge-appointment');
                    if (sbAppt) {
                        const pendingAppts = metrics.pending_appointments ?? 0;
                        if (pendingAppts > 0) {
                            sbAppt.textContent = pendingAppts;
                            sbAppt.classList.remove('hidden');
                        } else {
                            sbAppt.classList.add('hidden');
                        }
                    }

                    const sbQueue = document.getElementById('sidebar-badge-queue');
                    if (sbQueue) {
                        if ((metrics.active_queue || 0) > 0) {
                            sbQueue.textContent = metrics.active_queue;
                            sbQueue.classList.remove('hidden');
                        } else {
                            sbQueue.classList.add('hidden');
                        }
                    }

                    const sbMach = document.getElementById('sidebar-badge-machines');
                    if (sbMach) {
                        sbMach.textContent = `${metrics.machines_ready ?? 0}/${metrics.total_machines ?? 0}`;
                        sbMach.classList.remove('hidden');
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
                    ? `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">2-Day Economy Batch</span>`
                    : (isExpress ? `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-sky-50 text-[#0284C7] border border-sky-200">24h Express</span>`
                        : `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-slate-100 text-slate-600">Standard</span>`);

                const payStatus = act.payment_status || 'Paid';
                const isPaid = payStatus.toLowerCase() === 'paid';
                const payBadge = `<span class="px-2 py-0.5 text-[9px] font-extrabold rounded-full ${isPaid ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-200'}">${isPaid ? 'Paid' : 'Pending'}</span>`;

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

        // POS HELPERS, CHANGE CALCULATOR & VALIDATION
        function setPOSWeight(val) {
            const weightInput = document.getElementById('pos-weight');
            if (weightInput) {
                weightInput.value = val;
                updatePOSPreview(false);
            }
        }

        function calculatePOSChange() {
            const totalText = document.getElementById('pos-total')?.textContent || '₱0.00';
            const total = parseFloat(totalText.replace(/[^0-9.]/g, '')) || 0;
            const tenderedInput = document.getElementById('pos-tendered-input');
            const tendered = parseFloat(tenderedInput?.value || 0);
            const changeEl = document.getElementById('pos-change-due');
            if (!changeEl) return;

            if (tendered >= total && total > 0) {
                const change = tendered - total;
                changeEl.textContent = `₱${change.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                changeEl.className = 'text-sm font-black text-emerald-600 font-mono-num';
            } else if (tendered > 0 && total > 0) {
                const short = total - tendered;
                changeEl.textContent = `-₱${short.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (Short)`;
                changeEl.className = 'text-xs font-bold text-rose-600 font-mono-num';
            } else {
                changeEl.textContent = '₱0.00';
                changeEl.className = 'text-sm font-black text-slate-400 font-mono-num';
            }
        }

        function setPOSTendered(amount) {
            const tenderedInput = document.getElementById('pos-tendered-input');
            if (tenderedInput) {
                tenderedInput.value = amount;
                calculatePOSChange();
            }
        }

        function setPOSTenderedExact() {
            const totalText = document.getElementById('pos-total')?.textContent || '₱0.00';
            const total = parseFloat(totalText.replace(/[^0-9.]/g, '')) || 0;
            const tenderedInput = document.getElementById('pos-tendered-input');
            if (tenderedInput) {
                tenderedInput.value = Math.ceil(total);
                calculatePOSChange();
            }
        }

        function loadMachineInPOS(machineId) {
            switchTab('pos');
            const posSelect = document.getElementById('pos-machine');
            if (posSelect) {
                posSelect.value = String(machineId);
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

            calculatePOSChange();
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
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            weight, customer_email, customer_name, payment_status,
                            service_code, addons, machine_id, cycle_type
                        })
                    });
                    const sale = result.data;
                    showToast(`Sale recorded (TRX-${String(sale.transaction_id).padStart(4, '0')})! Machine started/queued.`, 'success');
                    nameInput.value = '';
                    emailInput.value = '';
                    const tenderedInput = document.getElementById('pos-tendered-input');
                    if (tenderedInput) tenderedInput.value = '';
                    document.querySelectorAll('input[name="pos_addons"]').forEach(cb => cb.checked = false);
                    updatePOSPreview(false);
                    fetchRealtimeData();
                    loadQueue();
                    loadMachines();
                }
            });
        }

        // MACHINE FLEET TELEMETRY & FILTER CONTROLS
        let loadedMachinesData = [];
        let currentMachineFilter = 'all';

        function setMachineFilter(filterKey, element) {
            currentMachineFilter = filterKey;
            document.querySelectorAll('.m-filter-btn').forEach(btn => {
                btn.className = 'm-filter-btn px-3.5 py-1.5 rounded-xl font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] transition';
            });
            if (element) {
                element.className = 'm-filter-btn px-3.5 py-1.5 rounded-xl font-bold bg-[#0284C7] text-white text-[11px] transition shadow-xs';
            }
            renderMachinesGrid();
        }

        function filterMachinesGrid() {
            renderMachinesGrid();
        }

        function renderMachinesGrid() {
            const grid = document.getElementById('machine-status-grid');
            if (!grid) return;
            const searchVal = (document.getElementById('machine-search-input')?.value || '').trim().toLowerCase();

            const filtered = (loadedMachinesData || []).filter(m => {
                const nameLower = (m.name || '').toLowerCase();
                const isDryer = m.capacity_kg === 13 || nameLower.includes('titan') || nameLower.includes('dry');
                const isWasher = !isDryer;

                if (currentMachineFilter === 'washers' && !isWasher) return false;
                if (currentMachineFilter === 'dryers' && !isDryer) return false;
                if (currentMachineFilter === 'available' && m.status !== 'available') return false;
                if (currentMachineFilter === 'inuse' && !['washing', 'drying', 'in-use'].includes(m.status)) return false;

                if (searchVal) {
                    const matchName = nameLower.includes(searchVal);
                    const matchCust = (m.customer_name || '').toLowerCase().includes(searchVal);
                    if (!matchName && !matchCust) return false;
                }
                return true;
            });

            if (!filtered.length) {
                grid.innerHTML = '<div class="col-span-full py-10 text-center text-slate-400 text-xs font-semibold bg-white rounded-2xl border border-slate-200/80">No machines match the selected filter.</div>';
                return;
            }

            grid.innerHTML = filtered.map(m => {
                const nameLower = (m.name || '').toLowerCase();
                const isDryer = m.capacity_kg === 13 || nameLower.includes('titan') || nameLower.includes('dry');
                const unitTypeLabel = isDryer ? '13kg Titan Dryer' : '8kg Regular Washer';

                const isAvailable = m.status === 'available';
                const isMaint = m.status === 'maintenance' || m.status === 'not_available';
                const isRunning = !isAvailable && !isMaint;

                let borderClass = 'border-slate-200 bg-white hover:border-[#0284C7]';
                let pillClass = 'bg-slate-100 text-slate-700 border-slate-200';
                let statusBadgeText = esc(m.status);

                if (isAvailable) {
                    borderClass = 'border-emerald-200/80 bg-emerald-50/30 hover:border-emerald-500';
                    pillClass = 'bg-emerald-100 text-emerald-800 border-emerald-200';
                    statusBadgeText = 'Available';
                } else if (isMaint) {
                    borderClass = 'border-rose-200/80 bg-rose-50/30';
                    pillClass = 'bg-rose-100 text-rose-800 border-rose-200';
                    statusBadgeText = 'Maintenance';
                } else if (isRunning) {
                    borderClass = 'border-sky-200/80 bg-sky-50/30 hover:border-sky-500';
                    pillClass = 'bg-sky-100 text-sky-800 border-sky-200';
                    statusBadgeText = m.status === 'washing' ? 'Washing' : (m.status === 'drying' ? 'Drying' : 'In-Use');
                }

                const queuedDetails = (m.queued_customers && m.queued_customers.length)
                    ? `<div class="mt-3 pt-2.5 border-t border-slate-200/70 text-[11px]">
                        <span class="font-bold text-slate-700 block mb-1">In Line Next (${m.queued_customers.length}):</span>
                        ${m.queued_customers.map(c => `<span class="text-slate-600 block truncate">#${c.queue_number} ${esc(c.customer_name)}</span>`).join('')}
                       </div>`
                    : '<p class="text-[10px] text-slate-400 mt-2.5">No queued customers waiting</p>';

                let actionBtn = '';
                if (isAvailable) {
                    actionBtn = `
                        <button onclick="event.stopPropagation(); loadMachineInPOS(${m.machine_id})" class="w-full mt-3 py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center justify-center gap-1.5 active:scale-95">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>
                            <span>Load Machine at Counter</span>
                        </button>
                    `;
                } else if (isRunning) {
                    actionBtn = `
                        <button onclick="event.stopPropagation(); switchTab('queue')" class="w-full mt-3 py-2 px-3 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold transition shadow-2xs flex items-center justify-center gap-1.5 active:scale-95">
                            <span>View in Queue</span>
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>
                        </button>
                    `;
                } else {
                    actionBtn = `
                        <span class="block w-full mt-3 py-2 text-center text-[11px] font-bold text-rose-600 bg-rose-100/60 rounded-xl">Offline for Maintenance</span>
                    `;
                }

                return `
                    <div class="app-card p-4 border ${borderClass} flex flex-col justify-between hover:shadow-md transition duration-200 group">
                        <div>
                            <div class="flex justify-between items-start mb-2">
                                <div>
                                    <div class="flex items-center gap-1.5">
                                        <div class="w-5 h-5 rounded-md ${isDryer ? 'bg-amber-50 text-amber-600' : 'bg-sky-50 text-[#0284C7]'} flex items-center justify-center flex-shrink-0">
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/></svg>
                                        </div>
                                        <h5 class="font-black text-sm text-slate-900 leading-tight">${esc(m.name)}</h5>
                                    </div>
                                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mt-0.5">${unitTypeLabel}</span>
                                </div>
                                <span class="px-2.5 py-0.5 text-[10px] font-extrabold rounded-full uppercase border ${pillClass} inline-flex items-center gap-1">
                                    <span class="w-1.5 h-1.5 rounded-full ${isAvailable ? 'bg-emerald-500' : (isMaint ? 'bg-rose-500' : 'bg-sky-500')}"></span>
                                    <span>${statusBadgeText}</span>
                                </span>
                            </div>
                            
                            <div class="p-2.5 bg-white/80 rounded-xl border border-slate-200/60 text-xs space-y-1 my-2.5">
                                <div class="flex justify-between text-slate-600">
                                    <span>Rate:</span>
                                    <span class="font-bold text-slate-900 font-mono-num">₱${Number(m.price_per_cycle).toFixed(2)}/cycle</span>
                                </div>
                                <div class="flex justify-between text-slate-600">
                                    <span>Current:</span>
                                    <span class="font-bold text-slate-800 truncate max-w-[130px]">${esc(m.customer_name || 'Idle / Open')}</span>
                                </div>
                            </div>

                            ${m.remaining_minutes ? `
                                <div class="mt-2 space-y-1.5">
                                    <div class="flex justify-between text-[11px] font-mono-num text-slate-700 font-bold">
                                        <span>Time Remaining:</span>
                                        <span class="text-[#0284C7] font-black">${m.remaining_minutes} mins</span>
                                    </div>
                                    <div class="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                                        <div class="h-full bg-[#0284C7] rounded-full transition-all duration-500" style="width: ${Math.max(12, Math.min(100, 100 - (m.remaining_minutes * 2.8)))}%"></div>
                                    </div>
                                </div>
                            ` : ''}

                            ${queuedDetails}
                        </div>
                        ${actionBtn}
                    </div>
                `;
            }).join('');
        }

        // LOAD MACHINES & RENDER STATUS GRID (WITH SKELETON LOADERS)
        async function loadMachines() {
            try {
                const result = await api('/api/machines');
                loadedMachinesData = Array.isArray(result.data) ? result.data : [];
                const machines = loadedMachinesData;

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
                        return `<option value="${m.machine_id}">${i === 0 ? 'Recommended: ' : ''}${esc(m.name)} (${m.capacity_kg}kg • ${statusLabel})</option>`;
                    }).join('') || '<option value="">No compatible machines available</option>';

                    if (compatible.some(m => String(m.machine_id) === previous)) posSelect.value = previous;
                }

                // Update Filter Badge Counts
                const availableCount = machines.filter(m => m.status === 'available').length;
                const inUseCount = machines.filter(m => ['washing', 'drying', 'in-use'].includes(m.status)).length;
                const countAll = document.getElementById('m-count-all');
                const countAvail = document.getElementById('m-count-available');
                const countInUse = document.getElementById('m-count-inuse');
                const fleetBadge = document.getElementById('machines-fleet-count-badge');

                if (countAll) countAll.textContent = machines.length;
                if (countAvail) countAvail.textContent = availableCount;
                if (countInUse) countInUse.textContent = inUseCount;
                if (fleetBadge) fleetBadge.textContent = `${machines.length} Units Active (${availableCount} Free)`;

                renderMachinesGrid();

                // Settings list for manager
                const settingsList = document.getElementById('machine-settings-list');
                if (settingsList) {
                    settingsList.innerHTML = machines.map(m => `
                        <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 items-center text-xs border border-slate-200 p-2.5 rounded-xl bg-white">
                            <input id="machine-name-${m.machine_id}" value="${esc(m.name)}" class="border border-slate-200 p-2 rounded-lg text-xs font-semibold">
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
                    ? `Taking this machine offline will immediately prevent it from accepting POS and online appointment loads.`
                    : `Updating pricing will apply to all subsequent counter checkout calculations.`,
                confirmText: 'Save Configuration',
                type: state === 'maintenance' ? 'warning' : 'default',
                onConfirm: async () => {
                    await api(`/api/machines/${id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
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

        // QUEUE MANAGEMENT & FILTER CONTROLS
        let loadedQueueData = [];
        let currentQueueFilter = 'all';

        function setQueueFilter(filterKey, element) {
            currentQueueFilter = filterKey;
            document.querySelectorAll('.q-filter-btn').forEach(btn => {
                btn.className = 'q-filter-btn px-3.5 py-1.5 rounded-xl font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] transition';
            });
            if (element) {
                element.className = 'q-filter-btn px-3.5 py-1.5 rounded-xl font-bold bg-[#0284C7] text-white text-[11px] transition shadow-xs';
            }
            renderQueueTable();
        }

        function filterQueueTable() {
            renderQueueTable();
        }

        const advancingQueueIds = new Set();

        function renderQueueTable() {
            const table = document.getElementById('queue-table-body');
            if (!table) return;
            const searchVal = (document.getElementById('queue-search-input')?.value || '').trim().toLowerCase();

            const items = (loadedQueueData || []).filter(item => {
                if (currentQueueFilter === 'waiting' && item.status !== 'Waiting') return false;
                if (currentQueueFilter === 'processing' && item.status !== 'Processing') return false;

                if (searchVal) {
                    const matchCust = (item.customer || '').toLowerCase().includes(searchVal);
                    const matchCode = (item.order_code || '').toLowerCase().includes(searchVal);
                    const matchMach = (item.machine || '').toLowerCase().includes(searchVal);
                    const matchNum = String(item.queue_number || '').includes(searchVal);
                    if (!matchCust && !matchCode && !matchMach && !matchNum) return false;
                }
                return true;
            });

            if (!items.length) {
                table.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-400 font-medium text-xs">No queue entries match the current filter or search.</td></tr>';
                return;
            }

            table.innerHTML = items.map(item => {
                const payMethod = item.payment_method || 'Cash';
                const payStatus = item.payment_status || 'Pending';
                const isPaid = payStatus.toLowerCase() === 'paid';
                const isCash = payMethod.toLowerCase().includes('cash');

                const paymentToggle = (currentRole !== 'Customer' && isCash && item.appointment_id) ? `
                    <button onclick="event.stopPropagation(); toggleOrderPaidStatus(${item.appointment_id}, '${payStatus}')" class="px-2.5 py-1 text-[10px] font-extrabold rounded-full ${isPaid ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-300'} hover:opacity-80 transition flex items-center gap-1.5 cursor-pointer" title="Click to Collect Cash / Toggle Payment">
                        <span class="w-1.5 h-1.5 rounded-full ${isPaid ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
                        <span>${esc(payStatus)}</span>
                    </button>
                ` : `
                    <span class="px-2.5 py-1 text-[10px] font-extrabold rounded-full ${isPaid ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-300'} inline-flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full ${isPaid ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
                        <span>${esc(payStatus)}</span>
                    </span>
                `;

                const isWaiting = item.status === 'Waiting';
                const isAdvancing = advancingQueueIds.has(item.queue_id);
                const actionButton = currentRole !== 'Customer' ? (
                    isAdvancing ? `
                        <button disabled class="px-3.5 py-1.5 bg-slate-100 border border-slate-200 text-slate-500 font-bold rounded-xl text-xs flex items-center gap-1.5 ml-auto cursor-not-allowed">
                            <svg class="w-3.5 h-3.5 animate-spin text-slate-600" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>
                            <span>${isWaiting ? 'Starting...' : 'Finishing...'}</span>
                        </button>
                    ` : (
                        isWaiting ? `
                            <button onclick="event.stopPropagation(); advanceQueue(${item.queue_id}, '${esc(item.customer)}', '${esc(item.status)}')" class="px-3.5 py-1.5 bg-[#0284C7] hover:bg-[#0369A1] text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 ml-auto active:scale-95 cursor-pointer">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                                <span>Start Machine</span>
                            </button>
                        ` : `
                            <button onclick="event.stopPropagation(); advanceQueue(${item.queue_id}, '${esc(item.customer)}', '${esc(item.status)}')" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 ml-auto active:scale-95 cursor-pointer">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5"/></svg>
                                <span>Finish Cycle</span>
                            </button>
                        `
                    )
                ) : '';

                return `
                <tr onclick="${item.appointment_id ? `openOrderDetailsModalById(${item.appointment_id})` : ''}" class="hover:bg-slate-50/80 cursor-pointer transition">
                    <td class="py-3.5 px-3">
                        <div class="w-9 h-9 rounded-xl ${item.status === 'Processing' ? 'bg-sky-50 text-[#0284C7] border border-sky-200' : 'bg-slate-100 text-slate-700'} flex items-center justify-center font-mono-num font-black text-xs shadow-2xs">
                            #${item.queue_number}
                        </div>
                    </td>
                    <td class="py-3.5 px-3">
                        <div class="font-extrabold text-slate-900 text-xs">${esc(item.customer)}</div>
                        <div class="flex items-center gap-1 mt-0.5">
                            <span class="text-[10px] text-slate-400 font-mono-num">${esc(item.order_code || 'WALK-IN')}</span>
                            ${item.appointment_id ? `<button onclick="event.stopPropagation(); copyOrderCode('${esc(item.order_code)}')" class="text-[9px] text-slate-400 hover:text-slate-700 transition" title="Copy ID"><svg class="w-3 h-3 inline" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg></button>` : ''}
                        </div>
                    </td>
                    <td class="py-3.5 px-3 text-slate-600 font-medium text-xs">${esc(item.service_type)}</td>
                    <td class="py-3.5 px-3">
                        <span class="font-bold text-[#0284C7] bg-sky-50 px-2.5 py-1 rounded-lg border border-sky-100 text-xs inline-block">${esc(item.machine)}</span>
                    </td>
                    <td class="py-3.5 px-3">
                        ${paymentToggle}
                    </td>
                    <td class="py-3.5 px-3">
                        <span class="px-2.5 py-1 text-[10px] font-bold rounded-full ${item.status === 'Processing' ? 'bg-sky-50 text-[#0284C7] border border-sky-200' : 'bg-amber-50 text-amber-700 border border-amber-200'} uppercase inline-flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full ${item.status === 'Processing' ? 'bg-[#0284C7]' : 'bg-amber-500'}"></span>
                            <span>${esc(item.status)} ${isWaiting ? `(~${item.estimated_waiting_time}m)` : ''}</span>
                        </span>
                    </td>
                    <td class="py-3.5 px-3 text-right" onclick="event.stopPropagation()">
                        ${actionButton}
                    </td>
                </tr>
            `}).join('');
        }

        async function loadQueue() {
            const table = document.getElementById('queue-table-body');
            if (!table) return;
            try {
                const queueResult = await api('/api/queue');
                loadedQueueData = Array.isArray(queueResult.data) ? queueResult.data : [];

                // Update KPI Cards
                const kpiTotal = document.getElementById('queue-kpi-total');
                const kpiWaiting = document.getElementById('queue-kpi-waiting');
                const kpiProcessing = document.getElementById('queue-kpi-processing');

                if (kpiTotal) kpiTotal.textContent = loadedQueueData.length;
                if (kpiWaiting) kpiWaiting.textContent = loadedQueueData.filter(i => i.status === 'Waiting').length;
                if (kpiProcessing) kpiProcessing.textContent = loadedQueueData.filter(i => i.status === 'Processing').length;

                renderQueueTable();
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
                    const result = await api('/api/queue', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
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
                    advancingQueueIds.add(id);
                    renderQueueTable();
                    try {
                        const res = await api(`/api/queue/${id}/advance`, { method: 'POST' });
                        showToast(res.message || 'Queue status updated', 'success');
                        await Promise.all([loadQueue(), loadAppointments(), loadMachines(), fetchRealtimeData()]);
                        if (currentModalOrder && currentModalOrder.queue_id === id) {
                            const freshAppt = loadedAppointmentsData.find(a => a.appointment_id === currentModalOrder.appointment_id);
                            if (freshAppt) openOrderDetailsModal(freshAppt);
                        }
                    } finally {
                        advancingQueueIds.delete(id);
                        renderQueueTable();
                    }
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

            const items = (Array.isArray(loadedAppointmentsData) ? loadedAppointmentsData : []).filter(item => {
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

            const headerNote = (currentApptTab === 'completed') ? `<div class="text-[11px] font-medium text-slate-400 pb-1 flex items-center justify-between"><span>Showing latest ${items.length} completed orders</span><span class="text-[10px] text-slate-400 font-mono-num">Sorted by latest</span></div>` : '';

            list.innerHTML = headerNote + items.map(item => {
                const sched = item.schedule_time ? new Date(item.schedule_time) : null;
                const formattedDate = (sched && !isNaN(sched)) ? sched.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Flexible';
                const formattedTime = (sched && !isNaN(sched)) ? sched.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : '';

                const isGraveyard = (item.priority_level || '').includes('Graveyard') || (item.turnaround_option || '').includes('2 Day');
                const isExpress = (item.priority_level || '').includes('Express') || (item.turnaround_option || '').includes('24');
                const priorityBadge = isGraveyard
                    ? `<span class="px-2.5 py-1 text-[10px] font-extrabold rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-2xs inline-flex items-center gap-1"><span>2-Day Economy Batch</span></span>`
                    : (isExpress ? `<span class="px-2.5 py-1 text-[10px] font-extrabold rounded-full bg-sky-50 text-[#0284C7] border border-sky-200 shadow-2xs inline-flex items-center gap-1"><span>24h Express</span></span>`
                        : `<span class="px-2.5 py-1 text-[10px] font-extrabold rounded-full bg-slate-100 text-slate-700 inline-flex items-center gap-1">Standard</span>`);

                const payMethod = item.payment_method || 'Cash';
                const payStatus = item.payment_status || 'Pending';
                const isPaid = payStatus.toLowerCase() === 'paid';
                const isCash = payMethod.toLowerCase().includes('cash');

                const fulfill = item.fulfillment_status || 'Waiting Drop-off';
                const isPickupDelivery = (item.order_mode || '').includes('Pick') || (item.service_type || '').includes('Pick');

                // Color-coded stage badge
                let stageStyle = 'bg-slate-100 text-slate-700 border-slate-200';
                const fLower = fulfill.toLowerCase();
                if (fLower.includes('for pickup')) {
                    stageStyle = 'bg-amber-50 text-amber-800 border-amber-200';
                } else if (fLower.includes('picked up')) {
                    stageStyle = 'bg-sky-50 text-sky-800 border-sky-200';
                } else if (fLower.includes('laundry')) {
                    stageStyle = 'bg-indigo-50 text-indigo-800 border-indigo-200';
                } else if (fLower.includes('delivery')) {
                    stageStyle = 'bg-purple-50 text-purple-800 border-purple-200';
                } else if (fLower.includes('ready')) {
                    stageStyle = 'bg-teal-50 text-teal-800 border-teal-200';
                } else if (fLower.includes('delivered') || fLower.includes('customer')) {
                    stageStyle = 'bg-emerald-50 text-emerald-800 border-emerald-200';
                }

                // Primary fulfillment action button
                let fulfillmentActionBtn = '';
                if (currentRole !== 'Customer' && item.status !== 'Completed' && item.status !== 'Cancelled') {
                    if (isPickupDelivery) {
                        if (fulfill === 'For Pickup') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); updateOrderFulfillment(${item.appointment_id}, 'Picked Up')" class="px-3.5 py-1.5 bg-[#0284C7] hover:bg-[#0369A1] text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 active:scale-95">
                                    <span>Pick Up by Staff</span>
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>
                                </button>
                            `;
                        } else if (fulfill === 'Picked Up' || fulfill === 'In Laundry' || item.status === 'Confirmed') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); updateOrderFulfillment(${item.appointment_id}, 'Out for Delivery')" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 active:scale-95">
                                    <span>Out for Delivery</span>
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>
                                </button>
                            `;
                        } else if (fulfill === 'Out for Delivery') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); updateOrderFulfillment(${item.appointment_id}, 'Delivered')" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 active:scale-95">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5"/></svg>
                                    <span>Mark Delivered</span>
                                </button>
                            `;
                        }
                    } else {
                        if (item.status === 'Pending' || fulfill === 'Waiting Drop-off') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); checkInAppointment(${item.appointment_id}, '${esc(item.customer)}')" class="px-3.5 py-1.5 bg-[#0284C7] hover:bg-[#0369A1] text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 active:scale-95">
                                    <span>Accept & Start</span>
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>
                                </button>
                            `;
                        } else if (fulfill === 'In Laundry' || item.status === 'Confirmed') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); updateOrderFulfillment(${item.appointment_id}, 'Ready for Pick-up')" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 active:scale-95">
                                    <span>Ready for Pick-up</span>
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>
                                </button>
                            `;
                        } else if (fulfill === 'Ready for Pick-up') {
                            fulfillmentActionBtn = `
                                <button onclick="event.stopPropagation(); completeAppointment(${item.appointment_id}, '${esc(item.customer)}')" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 active:scale-95">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5"/></svg>
                                    <span>Customer Picked Up</span>
                                </button>
                            `;
                        }
                    }
                }

                // Cash payment collect button
                let paymentToggleBtn = '';
                if (currentRole !== 'Customer' && isCash && !isPaid) {
                    paymentToggleBtn = `
                        <button onclick="event.stopPropagation(); toggleOrderPaidStatus(${item.appointment_id}, 'Pending')" class="px-3 py-1.5 text-xs font-black text-emerald-800 bg-emerald-100 hover:bg-emerald-200 border border-emerald-300 rounded-xl transition shadow-2xs flex items-center gap-1 active:scale-95">
                            <span>Collect ₱</span>
                        </button>
                    `;
                }

                return `
                    <div onclick="openOrderDetailsModalById(${item.appointment_id})" class="bg-white border border-slate-200/90 rounded-2xl p-4 sm:p-5 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 hover:border-[#0284C7] hover:shadow-md cursor-pointer transition duration-200 group">
                        <div class="flex items-start gap-4 flex-1 min-w-0">
                            <!-- Ticket Avatar -->
                            <div class="w-12 h-12 rounded-2xl ${item.status === 'Completed' ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-sky-50 text-[#0284C7] border border-sky-200'} flex flex-col items-center justify-center font-bold text-xs flex-shrink-0 shadow-2xs group-hover:scale-105 transition">
                                <span class="text-[9px] font-mono leading-none text-slate-400">TKT</span>
                                <span class="font-mono-num font-black text-sm">${item.queue_number ? `#${item.queue_number}` : 'ORD'}</span>
                            </div>

                            <!-- Details Column -->
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2 flex-wrap">
                                    <h4 class="text-sm font-black text-slate-900 truncate">${esc(item.customer)}</h4>
                                    <button onclick="event.stopPropagation(); copyOrderCode('${esc(item.order_code)}')" class="text-[10px] font-mono-num text-slate-600 bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded-md font-bold transition flex items-center gap-1" title="Click to copy Order ID">
                                        <span>${esc(item.order_code)}</span>
                                        <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                                    </button>
                                    ${priorityBadge}
                                    <span class="px-2.5 py-0.5 text-[10px] font-extrabold rounded-full border ${isPaid ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-800 border-amber-300'} inline-flex items-center gap-1.5">
                                        <span class="w-1.5 h-1.5 rounded-full ${isPaid ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
                                        <span>${esc(payMethod)} • ${esc(payStatus)}</span>
                                    </span>
                                </div>

                                <div class="text-xs text-slate-600 mt-1.5 flex items-center flex-wrap gap-2">
                                    <span class="font-extrabold text-slate-800">${esc(item.service_type || 'Laundry Service')}</span>
                                    <span class="text-slate-300">•</span>
                                    <span class="text-slate-600 font-medium">${formattedDate} at ${formattedTime}</span>
                                    ${item.pickup_time ? `<span class="text-slate-300">•</span><span class="text-slate-500 font-medium">Slot: ${esc(item.pickup_time)}</span>` : ''}
                                </div>

                                <div class="flex items-center gap-3 text-xs text-slate-500 mt-2 flex-wrap">
                                    <!-- Stage Pill -->
                                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${stageStyle} inline-flex items-center gap-1.5 shadow-2xs">
                                        <span class="w-1.5 h-1.5 rounded-full bg-slate-600"></span>
                                        <span>${esc(fulfill)}</span>
                                    </span>

                                    <!-- Mode -->
                                    <span class="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                                        ${isPickupDelivery ? 'Condo Delivery' : 'Drop-Off'}
                                    </span>

                                    <!-- Phone & Address -->
                                    ${item.phone_number ? `<a href="tel:${esc(item.phone_number)}" onclick="event.stopPropagation()" class="font-mono-num text-slate-700 hover:text-[#0284C7] font-semibold flex items-center gap-1"><svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>${esc(item.phone_number)}</a>` : ''}
                                    ${item.address && item.address !== '—' ? `<span class="text-slate-700 truncate max-w-[240px] font-medium flex items-center gap-1" title="${esc(item.address)}"><svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>${esc(item.address)}</span>` : ''}
                                </div>
                            </div>
                        </div>

                        <!-- Action Controls Area -->
                        <div class="flex items-center gap-2 self-end lg:self-center flex-shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100 w-full lg:w-auto justify-end" onclick="event.stopPropagation()">
                            ${paymentToggleBtn}
                            ${fulfillmentActionBtn}
                            <button onclick="openOrderDetailsModalById(${item.appointment_id})" class="px-3.5 py-1.5 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 text-slate-700 font-bold rounded-xl text-xs transition shadow-2xs flex items-center gap-1.5">
                                <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                                <span>Inspect</span>
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
                loadedAppointmentsData = Array.isArray(result.data) ? result.data : [];
                const counts = result.counts || { active: 0, completed: 0 };

                const countActive = document.getElementById('appt-count-active');
                const countCompleted = document.getElementById('appt-count-completed');
                if (countActive) countActive.textContent = counts.active;
                if (countCompleted) countCompleted.textContent = counts.completed;

                // Update Lobby KPI Strip Counters
                const activeOrders = loadedAppointmentsData.filter(item => item.status !== 'Completed' && item.status !== 'Cancelled');
                const pickupOrders = activeOrders.filter(item => (item.order_mode || '').toLowerCase().includes('pick') || (item.service_type || '').toLowerCase().includes('pick'));
                const dropoffOrders = activeOrders.filter(item => !((item.order_mode || '').toLowerCase().includes('pick') || (item.service_type || '').toLowerCase().includes('pick')));
                const unpaidOrders = activeOrders.filter(item => (item.payment_status || '').toLowerCase() !== 'paid');
                const transitOrders = activeOrders.filter(item => {
                    const f = (item.fulfillment_status || '').toLowerCase();
                    return f.includes('delivery') || f.includes('ready');
                });

                const kpiTotal = document.getElementById('appt-kpi-total');
                if (kpiTotal) kpiTotal.textContent = activeOrders.length;
                const kpiPickup = document.getElementById('appt-kpi-pickup');
                if (kpiPickup) kpiPickup.textContent = pickupOrders.length;
                const kpiDropoff = document.getElementById('appt-kpi-dropoff');
                if (kpiDropoff) kpiDropoff.textContent = dropoffOrders.length;
                const kpiUnpaid = document.getElementById('appt-kpi-unpaid');
                if (kpiUnpaid) kpiUnpaid.textContent = unpaidOrders.length;
                const kpiTransit = document.getElementById('appt-kpi-transit');
                if (kpiTransit) kpiTransit.textContent = transitOrders.length;

                renderFilteredAppointments();
            } catch (err) {
                console.error('Appointments load error:', err);
                list.innerHTML = `<div class="bg-slate-50 text-slate-500 rounded-2xl p-6 text-center text-xs font-semibold border border-slate-200">Unable to load appointments. <button onclick="loadAppointments()" class="text-[#0284C7] underline font-bold ml-1">Retry</button></div>`;
            }
        }

        function copyCurrentOrderId() {
            if (currentModalOrder && currentModalOrder.order_code) {
                copyOrderCode(currentModalOrder.order_code);
            }
        }

        function copyOrderCode(code) {
            if (!code) return;
            navigator.clipboard.writeText(code).then(() => {
                showToast(`Order ID copied: ${code}`, 'success');
            }).catch(() => {
                showToast(`Copied ${code}`, 'info');
            });
        }

        function openOrderDetailsModalById(appointmentId) {
            const found = loadedAppointmentsData.find(a => a.appointment_id === appointmentId);
            if (found) {
                openOrderDetailsModal(found);
            } else {
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

            const phoneLink = document.getElementById('modal-customer-phone-link');
            if (phoneLink) {
                phoneLink.textContent = order.phone_number || '—';
                phoneLink.href = order.phone_number ? `tel:${order.phone_number}` : '#';
            }

            document.getElementById('modal-customer-address').textContent = order.address || '—';
            document.getElementById('modal-service-type').textContent = order.service_type || 'Classic Wash, Dry, Fold';

            const isPickup = (order.order_mode || '').includes('Pick') || (order.service_type || '').includes('Pick');
            const modeBadge = document.getElementById('modal-order-mode-badge');
            if (modeBadge) modeBadge.textContent = isPickup ? 'Condo Delivery' : 'Drop-Off';

            const isGraveyard = (order.priority_level || '').includes('Graveyard') || (order.turnaround_option || '').includes('2 Day');
            document.getElementById('modal-turnaround-sla').textContent = isGraveyard ? '2 Days Economy (Graveyard Batch)' : '24 Hours Express';

            const payMethod = order.payment_method || 'Cash';
            const payStatus = order.payment_status || 'Pending';
            const isPaid = payStatus.toLowerCase() === 'paid';
            const isCash = payMethod.toLowerCase().includes('cash');

            document.getElementById('modal-payment-method').textContent = payMethod;
            const statusBadge = document.getElementById('modal-payment-status-badge');
            statusBadge.textContent = payStatus;
            statusBadge.className = isPaid
                ? 'px-2.5 py-1 text-xs font-black rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 inline-block mt-0.5'
                : 'px-2.5 py-1 text-xs font-black rounded-full bg-amber-100 text-amber-800 border border-amber-300 inline-block mt-0.5';

            const toggleBtn = document.getElementById('modal-payment-toggle-btn');
            const hint = document.getElementById('modal-payment-hint');
            if (isPaid) {
                toggleBtn.textContent = 'Revert to Pending';
                toggleBtn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold transition shadow-sm bg-slate-200 hover:bg-slate-300 text-slate-700';
                hint.textContent = isCash ? 'Cash payment collected & verified.' : 'Digital / Verified payment received.';
            } else {
                toggleBtn.textContent = 'Mark as Paid';
                toggleBtn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold transition shadow-sm bg-emerald-600 hover:bg-emerald-700 text-white';
                hint.textContent = 'Collect cash upon counter drop-off or doorstep delivery.';
            }

            const fulfill = order.fulfillment_status || 'Waiting Drop-off';
            document.getElementById('modal-fulfillment-badge').textContent = fulfill;
            const selectEl = document.getElementById('modal-fulfillment-select');
            if (selectEl) {
                selectEl.value = fulfill;
            }

            // Visual Lifecycle Stepper
            const fStatus = fulfill.toLowerCase();
            let currentStep = 1;
            if (fStatus.includes('picked up') || fStatus.includes('waiting')) currentStep = 2;
            if (fStatus.includes('in laundry') || order.status === 'Confirmed' || fStatus.includes('processing')) currentStep = 3;
            if (fStatus.includes('delivery') || fStatus.includes('ready')) currentStep = 4;
            if (fStatus.includes('delivered') || fStatus.includes('customer') || order.status === 'Completed') currentStep = 5;

            const steps = [
                { num: 1, label: 'Placed' },
                { num: 2, label: 'Collected' },
                { num: 3, label: 'In Wash' },
                { num: 4, label: 'Ready' },
                { num: 5, label: 'Done' }
            ];

            const stepperEl = document.getElementById('modal-stepper-container');
            if (stepperEl) {
                stepperEl.innerHTML = steps.map(s => {
                    const isDone = s.num < currentStep;
                    const isCurrent = s.num === currentStep;
                    let circleStyle = 'bg-slate-100 text-slate-400 border-slate-200';
                    if (isDone) circleStyle = 'bg-emerald-500 text-white border-emerald-500 shadow-xs';
                    if (isCurrent) circleStyle = 'bg-[#0284C7] text-white border-[#0284C7] ring-4 ring-sky-100 shadow-xs';

                    return `
                        <div class="flex flex-col items-center gap-1">
                            <div class="w-6 h-6 rounded-full border-2 ${circleStyle} flex items-center justify-center text-[10px] font-black transition">
                                ${isDone ? '✓' : s.num}
                            </div>
                            <span class="text-[9px] font-extrabold ${isCurrent ? 'text-[#0284C7]' : (isDone ? 'text-slate-700' : 'text-slate-400')} leading-tight">${s.label}</span>
                        </div>
                    `;
                }).join('');
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
                    headers: { 'Content-Type': 'application/json' },
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
                    headers: { 'Content-Type': 'application/json' },
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
                    const res = await api(`/api/appointments/${id}/check-in`, { method: 'POST' });
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
                    const res = await api(`/api/appointments/${id}/complete`, { method: 'POST' });
                    showToast(res.message, 'success');
                    await Promise.all([loadAppointments(), fetchRealtimeData(), loadQueue(), loadMachines()]);
                }
            });
        }

        function cancelAppointment(id, customerName) {
            showConfirmModal({
                title: 'Cancel Scheduled Appointment',
                message: `Are you sure you want to cancel the appointment for "${customerName}"?`,
                consequence: 'This permanently frees the scheduled machine slot and removes the reservation from the daily calendar.',
                confirmText: 'Yes, Cancel Appointment',
                type: 'danger',
                onConfirm: async () => {
                    const res = await api(`/api/appointments/${id}/cancel`, { method: 'POST' });
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
                    if (elToday) elToday.textContent = `₱${metrics.today_gross.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
                    if (elTodaySub) elTodaySub.textContent = `${metrics.today_count} checkouts • ${metrics.today_weight} kg`;
                    if (elWeek) elWeek.textContent = `₱${metrics.week_gross.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
                    if (elMonth) elMonth.textContent = `₱${metrics.month_gross.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
                    if (elAll) elAll.textContent = `₱${metrics.all_time_gross.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
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
                        <td class="py-3 px-3 font-bold text-emerald-600 font-mono-num">₱${day.paid_sales.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                        <td class="py-3 px-3 ${day.unpaid_sales > 0 ? 'text-amber-600 font-bold' : 'text-slate-400'} font-mono-num">₱${day.unpaid_sales.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                        <td class="py-3 px-3 font-black text-[#0284C7] font-mono-num">₱${day.gross_sales.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                        <td class="py-3 px-3">
                            <span class="px-2.5 py-0.5 text-[9px] font-bold rounded-full ${day.unpaid_sales === 0 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'} uppercase">
                                ${day.tally_status}
                            </span>
                        </td>
                        <td class="py-3 px-3 text-right">
                            <button onclick="drillDownSalesDay('${day.date}', '${day.display_date}')" class="px-3 py-1 bg-slate-100 hover:bg-[#0284C7] hover:text-white rounded-lg text-xs font-bold text-slate-700 transition">
                                View Receipts
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
                            ₱${sale.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
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
                                Assign Machine
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
                consequence: 'This dispatches the customer directly to the next free washer with minimal queue wait.',
                confirmText: 'Assign Machine',
                type: 'default',
                onConfirm: async () => {
                    const result = await api('/api/manager/ghost-slots/assign', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
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
                        headers: { 'Content-Type': 'application/json' },
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
            const initialLabels = [];
        const initialHistorical = [];
        const initialPredicted = [];

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
    