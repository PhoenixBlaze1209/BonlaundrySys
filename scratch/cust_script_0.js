
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

        function showConfirmModal({ title, message, consequence, confirmText = 'Confirm', onConfirm }) {
            const modal = document.getElementById('confirm-modal');
            const titleEl = document.getElementById('confirm-modal-title');
            const descEl = document.getElementById('confirm-modal-desc');
            const consEl = document.getElementById('confirm-modal-consequence-text');
            const confirmBtn = document.getElementById('confirm-modal-confirm-btn');
            const cancelBtn = document.getElementById('confirm-modal-cancel-btn');

            if (!modal) return;
            if (titleEl) titleEl.textContent = title;
            if (descEl) descEl.textContent = message;
            if (consEl) consEl.textContent = consequence;
            if (confirmBtn) confirmBtn.textContent = confirmText;

            modal.classList.remove('hidden');

            const handleConfirm = async () => {
                cleanup();
                if (typeof onConfirm === 'function') await onConfirm();
            };

            const cleanup = () => {
                modal.classList.add('hidden');
                confirmBtn?.removeEventListener('click', handleConfirm);
                cancelBtn?.removeEventListener('click', cleanup);
            };

            confirmBtn?.addEventListener('click', handleConfirm);
            cancelBtn?.addEventListener('click', cleanup);
        }

        const esc = s => String(s || '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');

        async function api(url, options = {}) {
            const res = await fetch(url, options);
            const data = await res.json();
            if (!res.ok) throw new Error(data.message || 'Server request failed');
            return data;
        }

        async function loadDashboard() {
            try {
                const [summaryRes, apptRes] = await Promise.all([
                    api('/api/dashboard/summary'),
                    api('/api/appointments')
                ]);

                const summaryData = summaryRes.data || {};
                const metrics = summaryData.metrics || {};
                const appointments = Array.isArray(apptRes.data) ? apptRes.data : [];

                // Find active queue from customer appointments
                const activeApptWithQueue = appointments.find(a => a.queue_number && a.status !== 'Completed' && a.status !== 'Cancelled');
                const queueNum = activeApptWithQueue ? `#${activeApptWithQueue.queue_number}` : '—';
                const waitTime = activeApptWithQueue ? `~${metrics.est_wait_time_mins || 0}m` : `~${metrics.est_wait_time_mins || 0}m`;

                const readableStatus = v => String(v || 'Pending').replaceAll('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

                const waitEl = document.getElementById('queue-wait');
                if (waitEl) waitEl.textContent = waitTime;

                const numEl = document.getElementById('queue-number');
                if (numEl) numEl.textContent = queueNum;

                const queueCard = document.getElementById('my-queue-card');
                if (queueCard) {
                    if (activeApptWithQueue) {
                        queueCard.innerHTML = `
                            <p class="text-xl font-extrabold text-slate-900">Queue #${activeApptWithQueue.queue_number} &bull; <span class="text-[#0284C7]">${esc(readableStatus(activeApptWithQueue.status))}</span></p>
                            <p class="text-xs text-slate-600 font-medium">${esc(activeApptWithQueue.service_type || 'Laundry load')} &bull; estimated wait ${metrics.est_wait_time_mins || 0} mins</p>
                        `;
                    } else {
                        queueCard.innerHTML = `
                            <p class="text-lg font-bold text-slate-800">No active queue</p>
                            <p class="text-xs text-slate-500">Book a visit below when you are ready to drop off garments.</p>
                        `;
                    }
                }

                const countEl = document.getElementById('appointment-count');
                if (countEl) countEl.textContent = appointments.length;

                const listEl = document.getElementById('appointment-list');
                if (listEl) {
                    if (!appointments.length) {
                        listEl.innerHTML = '<div class="rounded-xl bg-slate-50 p-4 text-xs text-slate-400 text-center">No appointments booked yet.</div>';
                    } else {
                        listEl.innerHTML = appointments.map(item => {
                            const isGraveyard = (item.priority_level || '').includes('Graveyard') || (item.turnaround_option || '').includes('2 Day');
                            const payMethod = item.payment_method || 'Cash';
                            const payStatus = item.payment_status || 'Pending';
                            const isPaid = payStatus.toLowerCase() === 'paid';
                            const fulfill = item.fulfillment_status || 'Waiting Drop-off';
                            const serviceName = String(item.service_type || 'Laundry Service').replaceAll('-', ' ');
                            const schedDateStr = item.schedule_time ? new Date(item.schedule_time).toLocaleString() : 'Flexible / Pending';

                            return `
                            <article class="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between transition hover:border-slate-300">
                                <div class="space-y-1">
                                    <div class="flex flex-wrap items-center gap-1.5">
                                        <span class="font-mono text-xs font-black text-[#0284C7]">${esc(item.order_code || 'ORD')}</span>
                                        <span class="px-2 py-0.5 rounded-full text-[9px] font-extrabold ${isGraveyard ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-sky-50 text-[#0284C7] border border-sky-200'}">
                                            ${isGraveyard ? '2-Day Economy Batch' : '24h Express'}
                                        </span>
                                        <span class="px-2 py-0.5 rounded-full text-[9px] font-extrabold ${isPaid ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-200'}">
                                            ${esc(payMethod)} &bull; ${esc(payStatus)}
                                        </span>
                                    </div>
                                    <p class="font-bold text-slate-900 text-xs">${esc(serviceName)}</p>
                                    <p class="text-[11px] text-slate-500">${esc(schedDateStr)} &bull; <span class="text-sky-700 font-semibold">${esc(fulfill)}</span></p>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="w-fit rounded-full bg-slate-100 border border-slate-200 px-3 py-1 text-[10px] font-extrabold text-slate-700 uppercase">
                                        ${esc(readableStatus(item.status))}
                                    </span>
                                </div>
                            </article>
                        `}).join('');
                    }
                }

            } catch (err) {
                console.error('Customer dashboard load error:', err);
                const qCard = document.getElementById('my-queue-card');
                if (qCard) qCard.innerHTML = `<p class="text-xs text-slate-500 font-medium">No active queue entry right now.</p>`;
                const apptList = document.getElementById('appointment-list');
                if (apptList) apptList.innerHTML = `<div class="rounded-xl bg-slate-50 p-4 text-xs text-slate-400 text-center">No appointments found.</div>`;
            }
        }

        function handleServiceChange() {
            const mode = document.getElementById('cust-handling-mode').value;
            const pickupContainer = document.getElementById('cust-pickup-details');
            const bldgSelect = document.getElementById('cust-deca-building');
            const unitInput = document.getElementById('cust-deca-unit');

            if (mode === 'Pick-up & Delivery') {
                pickupContainer.classList.remove('hidden');
                bldgSelect.required = true;
                unitInput.required = true;
            } else {
                pickupContainer.classList.add('hidden');
                bldgSelect.required = false;
                unitInput.required = false;
            }
        }

        async function checkAvailability() {
            const val = document.getElementById('appointment-time').value;
            if (!val) return;
            const status = document.getElementById('availability');
            try {
                const res = await api(`/api/appointments/availability?schedule_time=${encodeURIComponent(val)}`);
                status.textContent = res.data.available ? `${res.data.available} of ${res.data.capacity} machines available at this time.` : 'This slot is fully booked. Please choose another time.';
                status.className = `text-[11px] mt-1 font-semibold ${res.data.available ? 'text-emerald-600' : 'text-rose-600'}`;
            } catch (err) {
                status.textContent = err.message;
                status.className = 'text-[11px] mt-1 font-semibold text-rose-600';
            }
        }

        document.getElementById('booking-form').addEventListener('submit', event => {
            event.preventDefault();
            const form = event.currentTarget;
            const timeVal = form.schedule_time.value;
            const modeVal = form.handling_mode.value;
            const packageVal = form.package_type.value;
            const phoneVal = form.phone_number.value.trim();

            if (!timeVal) {
                showToast('Please select a preferred date and time.', 'error');
                return;
            }

            const schedDate = new Date(timeVal);
            if (schedDate <= new Date()) {
                showToast('Appointment time must be in the future. Past times are not allowed.', 'error');
                document.getElementById('appointment-time')?.focus();
                return;
            }

            if (!phoneVal || phoneVal.length < 7) {
                showToast('Please enter a valid contact phone number.', 'error');
                document.getElementById('cust-phone')?.focus();
                return;
            }

            const combinedService = `${modeVal} — ${packageVal}`;
            const formattedTime = schedDate.toLocaleString();

            const consequenceText = (modeVal === 'Pick-up & Delivery')
                ? `Our staff will coordinate pickup on ${formattedTime}. Your order will be added to the live shop tracker.`
                : `This reserves an active washer slot at the shop for ${formattedTime}. Please drop off clothes within 15 minutes of your scheduled time.`;

            const payload = Object.fromEntries(new FormData(form));
            payload.service_type = combinedService;

            showConfirmModal({
                title: 'Confirm Appointment Booking',
                message: `Book ${combinedService} for ${formattedTime}?`,
                consequence: consequenceText,
                confirmText: 'Book Appointment',
                onConfirm: async () => {
                    const result = await api('/customer/book', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                    showToast(`Appointment booked! Your Ticket is #${result.queue_number} (Order ID: ${result.order_id})`, 'success');
                    form.reset();
                    document.getElementById('availability').textContent = 'Select a date and time to verify availability.';
                    document.getElementById('availability').className = 'text-[11px] text-slate-400 mt-1';
                    await loadDashboard();
                }
            });
        });

        // Set minimum schedule time to now
        const appointmentTime = document.getElementById('appointment-time');
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        appointmentTime.min = now.toISOString().slice(0, 16);

        loadDashboard();
        setInterval(loadDashboard, 30000);
    