// frontend/js/admin.js

const BASE_URL = 'http://localhost:8000/v1'; // آدرس پایه API شما
const dataContainer = document.getElementById('data-container'); // عنصری که داده‌ها در آن نمایش داده می‌شوند
const token = localStorage.getItem('access_token'); // توکن احراز هویت کاربر

let currentView = 'pending_jobs'; // نمای فعلی (مثلاً 'pending_jobs', 'job', 'user', 'city' و...)
let allJobsData = []; // متغیری برای نگهداری تمام شغل‌ها که از سرور دریافت می‌شود

// --- توابع کمکی ---

/**
 * نمایش یک پیام سیستمی در بخش نمایش داده‌ها.
 * @param {string} message - متنی که باید نمایش داده شود.
 * @param {boolean} isError - اگر true باشد، پیام با رنگ قرمز نمایش داده می‌شود.
 */
function showSystemMessage(message, isError = false) {
    dataContainer.innerHTML = `<p class="system-msg" style="color:${isError ? 'red' : '#666'};">${message}</p>`;
}

/**
 * پس از بارگذاری کامل DOM، این تابع اجرا می‌شود.
 * وضعیت احراز هویت ادمین را بررسی کرده و سپس مشاغل در انتظار تأیید را بارگذاری می‌کند.
 */
document.addEventListener("DOMContentLoaded", async () => {
    const user = JSON.parse(localStorage.getItem('user')); // اطلاعات کاربر را از localStorage می‌گیرد
    if (!token || !user || !user.is_admin) { // بررسی می‌کند که توکن و اطلاعات کاربر موجود باشد و کاربر ادمین باشد
        alert("❌ فقط مدیران به این صفحه دسترسی دارند. لطفاً وارد حساب ادمین خود شوید."); // هشدار دسترسی
        window.location.href = "login.html"; // به صفحه ورود هدایت می‌کند
        return;
    }
    console.log("DOM Loaded. Initializing with pending jobs."); // لاگ کنسول
    await fetchAllJobsAndRender('pending_jobs'); // تمام مشاغل را دریافت و سپس مشاغل در انتظار را رندر می‌کند
});

/**
 * کاربر را از سیستم خارج کرده و به صفحه اصلی هدایت می‌کند.
 */
function logout() {
    localStorage.removeItem('access_token'); // توکن دسترسی را حذف می‌کند
    localStorage.removeItem('token_type'); // نوع توکن را حذف می‌کند
    localStorage.removeItem('user'); // اطلاعات کاربر را حذف می‌کند
    window.location.href = 'index.html'; // به صفحه اصلی هدایت می‌کند
}

// --- توابع دریافت و رندر داده‌ها ---

/**
 * تمام مشاغل را از API ادمین دریافت کرده و در allJobsData ذخیره می‌کند.
 * @returns {Promise<Array>} - لیستی از تمام مشاغل.
 * @throws {Error} - در صورت بروز خطا در دریافت داده‌ها.
 */
async function fetchAllJobs() {
    console.log(`Fetching ALL jobs from admin/jobs/all`);
    const headers = { 'Authorization': `Bearer ${token}` };
    try {
        const response = await fetch(`${BASE_URL}/admin/jobs/all`, { headers });
        if (!response.ok) {
            const errorText = await response.text();
            if (response.status === 403 || response.status === 401) {
                throw new Error(`دسترسی غیرمجاز. توکن منقضی شده است. جزئیات: ${errorText}`);
            }
            throw new Error(`خطا در دریافت تمام شغل‌ها: ${response.status} - ${errorText}`);
        }
        const data = await response.json();
        console.log(`ALL Jobs data received:`, data); // لاگ داده‌های دریافت شده
        allJobsData = data; // ذخیره تمام شغل‌ها در متغیر سراسری
        return data; // بازگرداندن داده‌ها
    } catch (error) {
        console.error(`Error in fetchAllJobs:`, error); // لاگ خطا
        throw error; // پرتاب خطا
    }
}

/**
 * رندر کردن لیست شهرها در DOM.
 * @param {Array} cities - آرایه‌ای از اشیاء شهرها.
 */
function renderCities(cities) {
    if (!cities || cities.length === 0) {
        return showSystemMessage('هیچ شهری یافت نشد.');
    }
    dataContainer.innerHTML = cities.map(city => `
        <div class="card">
            <h3>شهر: ${city.name}</h3>
        </div>
    `).join('');
    console.log("Cities rendered.");
}

/**
 * رندر کردن لیست کاربران در DOM.
 * @param {Array} users - آرایه‌ای از اشیاء کاربران.
 */
function renderUsers(users) {
    if (!users || users.length === 0) {
        return showSystemMessage('هیچ کاربری یافت نشد.');
    }
    dataContainer.innerHTML = users.map(user => `
        <div class="card">
            <h3>${user.first_name} ${user.last_name} (${user.username})</h3>
            <p><strong>نقش:</strong> ${user.is_admin ? 'مدیر' : ''} ${user.is_employer ? 'کارفرما' : ''} ${!user.is_admin && !user.is_employer ? 'کارجو' : ''}</p>
            <p><strong>استان:</strong> ${user.province}</p>
        </div>
    `).join('');
    console.log("Users rendered.");
}

/**
 * رندر کردن لیست شغل‌ها در DOM، با قابلیت فیلتر کردن برای نمایش شغل‌های در انتظار یا تأیید شده.
 * @param {boolean} isPendingView - اگر true باشد، فقط مشاغل در انتظار تأیید را نمایش می‌دهد.
 */
function renderJobs(isPendingView) {
    let filteredJobs;
    if (isPendingView) {
        filteredJobs = allJobsData.filter(job => !job.is_approved); // فیلتر کردن مشاغل در انتظار
        console.log("Filtered pending jobs (from allJobsData):", filteredJobs);
    } else {
        filteredJobs = allJobsData.filter(job => job.is_approved); // فیلتر کردن مشاغل تأیید شده
        console.log("Filtered approved jobs (from allJobsData):", filteredJobs);
    }

    if (!filteredJobs || filteredJobs.length === 0) {
        return showSystemMessage(isPendingView ? 'هیچ شغل در انتظار تأییدی یافت نشد.' : 'هیچ شغل تأیید شده‌ای یافت نشد.');
    }
    
    dataContainer.innerHTML = filteredJobs.map(job => {
        const statusText = job.is_approved ? 'تأیید شده' : 'در انتظار تأیید'; // متن وضعیت
        const statusClass = job.is_approved ? 'status-approved' : 'status-pending'; // کلاس CSS وضعیت

        let actionButtons = '';
        if (isPendingView) {
            actionButtons = `
                <button class="approve" onclick="updateJobStatus(${job.id}, true)">تأیید</button>
                <button class="delete" onclick="deleteJob(${job.id}, 'pending_jobs')">حذف</button>
            `; // دکمه‌های تأیید و حذف برای مشاغل در انتظار
        } else {
            actionButtons = `<button class="delete" onclick="deleteJob(${job.id}, 'job')">حذف</button>`; // دکمه حذف برای مشاغل تأیید شده
        }

        return `
            <div class="card" id="job-card-${job.id}">
                <h3>${job.title}</h3>
                <p><strong>کارفرما:</strong> ${job.employer?.first_name || 'نامشخص'} ${job.employer?.last_name || ''}</p>
                <p><strong>شهر:</strong> ${job.city?.name || 'نامشخص'}</p>
                <p><strong>توضیحات:</strong> ${job.description.substring(0, 100)}...</p>
                <p><strong>وضعیت:</strong> <span class="${statusClass}">${statusText}</span></p>
                <div class="actions">
                    ${actionButtons}
                </div>
            </div>`; // ساخت کارت شغل
    }).join('');
    console.log("Jobs rendered based on allJobsData.");
}

/**
 * لیست درخواست‌های شغلی کاربران را در DOM رندر می‌کند.
 * @param {Array} userJobs - آرایه‌ای از اشیاء درخواست‌های شغلی.
 */
function renderUserJobApplications(userJobs) {
    if (!userJobs || userJobs.length === 0) {
        return showSystemMessage('هیچ درخواست شغلی یافت نشد.');
    }
    dataContainer.innerHTML = userJobs.map(req => `
        <div class="card">
            <h3>درخواست شغل</h3>
            <p><strong>شناسه کاربر:</strong> ${req.user_id}</p>
            <p><strong>شناسه شغل:</strong> ${req.job_id}</p>
        </div>
    `).join('');
    console.log("User job applications rendered.");
}

/**
 * تابع اصلی برای دریافت و نمایش داده‌ها بر اساس نوع درخواستی.
 * این تابع بسته به نوع، یا از allJobsData استفاده می‌کند یا مستقیماً از API درخواست می‌دهد.
 * @param {string} type - نوع داده‌ای که باید نمایش داده شود ('city', 'user', 'job', 'pending_jobs', 'user_job_applications').
 */
async function fetchAndRenderData(type) {
    currentView = type; // به‌روزرسانی نمای فعلی
    showSystemMessage('⏳ در حال بارگذاری...'); // نمایش پیام بارگذاری
    console.log(`Changing view to: ${currentView}`);
    try {
        if (type === 'city') {
            const data = await fetchDataNonJob(type); // دریافت داده‌های شهر
            renderCities(data); // رندر کردن شهرها
        } else if (type === 'user') {
            const data = await fetchDataNonJob(type); // دریافت داده‌های کاربر
            renderUsers(data); // رندر کردن کاربران
        } else if (type === 'job') {
            renderJobs(false); // رندر مشاغل تأیید شده از allJobsData
        } else if (type === 'pending_jobs') {
            renderJobs(true); // رندر مشاغل در انتظار تأیید از allJobsData
        } else if (type === 'user_job_applications') {
            const data = await fetchDataNonJob(type); // دریافت داده‌های درخواست شغلی
            renderUserJobApplications(data); // رندر کردن درخواست‌های شغلی
        }
    } catch (err) {
        console.error("Error during fetchAndRenderData:", err);
        showSystemMessage(`❌ خطا: ${err.message}`, true);
        if (err.message.includes("توکن منقضی شده") || err.message.includes("دسترسی غیرمجاز")) {
            setTimeout(() => {
                logout();
            }, 2000);
        }
    }
}

/**
 * تابع جدید برای دریافت داده‌های غیر شغل (شهرها، کاربران، درخواست‌های شغلی).
 * @param {string} type - نوع داده (مانند 'city', 'user', 'user_job_applications').
 * @returns {Promise<Array>} - آرایه‌ای از داده‌ها.
 * @throws {Error} - در صورت نامعتبر بودن نوع داده یا بروز خطا در API.
 */
async function fetchDataNonJob(type) {
    console.log(`Fetching non-job data for type: ${type}`);
    let endpoint = '';
    let requiresAuth = true;

    switch(type) {
        case 'city':
            endpoint = 'cities'; // نقطه پایانی برای شهرها
            requiresAuth = false; // احراز هویت نیاز ندارد
            break;
        case 'user':
            endpoint = 'admin/users'; // نقطه پایانی برای کاربران
            break;
        case 'user_job_applications':
            endpoint = 'admin/user-jobs'; // نقطه پایانی برای درخواست‌های شغلی
            break;
        default:
            throw new Error('نوع داده نامعتبر برای fetchDataNonJob.');
    }

    const headers = {};
    if (requiresAuth && token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${BASE_URL}/${endpoint}`, { headers });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`خطا در دریافت داده‌ها از ${endpoint}: ${response.status} - ${errorText}`);
        }
        const data = await response.json();
        console.log(`Non-job data received for ${type}:`, data);
        return data;
    } catch (error) {
        console.error(`Error in fetchDataNonJob for ${type}:`, error);
        throw error;
    }
}

/**
 * تمام مشاغل را از سرور واکشی کرده و سپس نمای فعلی را رندر می‌کند.
 * این تابع برای اطمینان از به‌روز بودن allJobsData قبل از رندر کردن استفاده می‌شود.
 * @param {string} viewToSwitchTo - نمایی که پس از واکشی داده‌ها باید رندر شود.
 */
async function fetchAllJobsAndRender(viewToSwitchTo) {
    showSystemMessage('⏳ در حال بارگذاری تمام شغل‌ها...');
    try {
        await fetchAllJobs(); // تمام مشاغل را از سرور دریافت و در allJobsData ذخیره می‌کند
        fetchAndRenderData(viewToSwitchTo); // نمای مورد نظر را با داده‌های تازه رندر می‌کند
    } catch (error) {
        showSystemMessage(`❌ خطا در بارگذاری شغل‌ها: ${error.message}`, true);
    }
}

/**
 * بر اساس نوع داده انتخابی، اقدام به دریافت و نمایش داده‌ها می‌کند.
 * اگر نوع، 'job' یا 'pending_jobs' باشد، ابتدا تمام مشاغل را دوباره واکشی می‌کند.
 * @param {string} type - نوع داده‌ای که باید نمایش داده شود.
 */
function showData(type) {
    if (type === 'job' || type === 'pending_jobs') { // اگر نمایش مشاغل بود
        fetchAllJobsAndRender(type); // تمام مشاغل را واکشی و رندر می‌کند
    } else {
        fetchAndRenderData(type); // داده‌های غیر شغل را مستقیماً دریافت و رندر می‌کند
    }
}

// --- توابع عملیات (تأیید، حذف) ---

/**
 * وضعیت تأیید یک شغل را به‌روزرسانی می‌کند.
 * پس از موفقیت، تمام مشاغل را دوباره از سرور واکشی کرده و نمای مربوطه را رندر می‌کند.
 * @param {number} jobId - شناسه شغل.
 * @param {boolean} isApproved - وضعیت تأیید جدید (true برای تأیید، false برای رد).
 */
async function updateJobStatus(jobId, isApproved) {
    try {
        console.log(`Attempting to update job ${jobId} to is_approved: ${isApproved}`);
        const response = await fetch(`${BASE_URL}/admin/jobs/${jobId}`, { // ارسال درخواست PUT
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ is_approved: isApproved }) // ارسال وضعیت جدید
        });

        if (!response.ok) { // بررسی موفقیت‌آمیز بودن پاسخ
            const errorData = await response.json();
            throw new Error(errorData.detail || `خطا در به‌روزرسانی وضعیت شغل ${jobId}.`);
        }

        alert(`✅ شغل ${jobId} با موفقیت ${isApproved ? 'تأیید' : 'رد'} شد!`);
        console.log(`Job ${jobId} updated successfully. Now re-fetching all jobs to ensure consistency.`);
        
        // ⭐️⭐️⭐️⭐️⭐️ تغییر کلیدی: به جای آپدیت محلی، کل مشاغل رو از سرور دوباره بگیر ⭐️⭐️⭐️⭐️⭐️
        await fetchAllJobsAndRender(isApproved ? 'job' : currentView); // دوباره واکشی و رندر

    } catch (error) {
        console.error("Error updating job status:", error);
        alert("❌ خطا: " + error.message);
    }
}

/**
 * یک شغل را حذف می‌کند.
 * پس از موفقیت، تمام مشاغل را دوباره از سرور واکشی کرده و نمای مربوطه را رندر می‌کند.
 * @param {number} jobId - شناسه شغل.
 * @param {string} viewToRefresh - نمایی که پس از حذف باید رفرش شود.
 */
async function deleteJob(jobId, viewToRefresh) {
    if (!confirm("آیا از حذف این شغل اطمینان دارید؟")) { // درخواست تأیید از کاربر
        return;
    }
    try {
        console.log(`Attempting to delete job ${jobId}.`);
        const response = await fetch(`${BASE_URL}/admin/jobs/${jobId}`, { // ارسال درخواست DELETE
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) { // بررسی موفقیت‌آمیز بودن پاسخ
            const errorData = await response.json();
            throw new Error(errorData.detail || `خطا در حذف شغل ${jobId}.`);
        }

        alert(`✅ شغل ${jobId} با موفقیت حذف شد!`);
        console.log(`Job ${jobId} deleted successfully. Now re-fetching all jobs to ensure consistency.`);
        
        // ⭐️⭐️⭐️⭐️⭐️ تغییر کلیدی: به جای آپدیت محلی، کل مشاغل رو از سرور دوباره بگیر ⭐️⭐️⭐️⭐️⭐️
        async function updateJobStatus(jobId, isApproved) {
            try {
                
                alert(`✅ شغل ${jobId} با موفقیت ${isApproved ? 'تأیید' : 'رد'} شد!`);
                console.log(`Job ${jobId} updated successfully. Now re-fetching all jobs to ensure consistency.`);
        
                // ❗️ اصلاح مهم: همیشه همون نمای فعلی رو حفظ کن
                await fetchAllJobsAndRender(currentView); 
        
            } catch (error) {
               
            }
        }
        ;

    } catch (error) {
        console.error("Error deleting job:", error);
        alert("❌ خطا: " + error.message);
    }
}