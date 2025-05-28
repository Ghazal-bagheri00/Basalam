// admin.js

const BASE_URL = 'http://localhost:8000/v1';
const dataContainer = document.getElementById('data-container');
const token = localStorage.getItem('access_token');

let currentView = 'pending_jobs';
let allJobsData = [];

// --- توابع کمکی ---

function showSystemMessage(message, isError = false) {
    dataContainer.innerHTML = `<p class="system-msg" style="color:${isError ? 'red' : '#666'};">${message}</p>`;
}

document.addEventListener("DOMContentLoaded", async () => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!token || !user || !user.is_admin) {
        alert("❌ فقط مدیران به این صفحه دسترسی دارند. لطفاً وارد حساب ادمین خود شوید.");
        window.location.href = "login.html";
        return;
    }
    console.log("DOM Loaded. Initializing with pending jobs.");
    await fetchAllJobsAndRender('pending_jobs');
});

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// --- توابع دریافت و رندر داده‌ها ---

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
        console.log(`ALL Jobs data received:`, data);
        allJobsData = data;
        return data;
    } catch (error) {
        console.error(`Error in fetchAllJobs:`, error);
        throw error;
    }
}

/**
 * رندر کردن لیست شهرها در DOM.
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
 * @param {boolean} isPendingView - اگر true باشد، فقط شغل‌های در انتظار تأیید را نمایش می‌دهد.
 */
function renderJobs(isPendingView) {
    let filteredJobs;
    if (isPendingView) {
        filteredJobs = allJobsData.filter(job => !job.is_approved);
        console.log("Filtered pending jobs (from allJobsData):", filteredJobs);
    } else {
        filteredJobs = allJobsData.filter(job => job.is_approved);
        console.log("Filtered approved jobs (from allJobsData):", filteredJobs);
    }

    if (!filteredJobs || filteredJobs.length === 0) {
        return showSystemMessage(isPendingView ? 'هیچ شغل در انتظار تأییدی یافت نشد.' : 'هیچ شغل تأیید شده‌ای یافت نشد.');
    }
    
    dataContainer.innerHTML = filteredJobs.map(job => {
        const statusText = job.is_approved ? 'تأیید شده' : 'در انتظار تأیید';
        const statusClass = job.is_approved ? 'status-approved' : 'status-pending';

        let actionButtons = '';
        if (isPendingView) {
            actionButtons = `
                <button class="approve" onclick="updateJobStatus(${job.id}, true)">تأیید</button>
                <button class="delete" onclick="deleteJob(${job.id}, 'pending_jobs')">حذف</button>
            `;
        } else {
            actionButtons = `<button class="delete" onclick="deleteJob(${job.id}, 'job')">حذف</button>`;
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
            </div>`;
    }).join('');
    console.log("Jobs rendered based on allJobsData.");
}

function renderUserJobApplications(userJobs) {
    if (!userJobs || userJobs.length === 0) {
        return showSystemMessage('هیچ درخواست شغلی یافت نشد.');
    }
    dataContainer.innerHTML = userJobs.map(req => {
        const userName = req.user ? `${req.user.first_name} ${req.user.last_name}` : 'نامشخص';
        const jobTitle = req.job ? req.job.title : 'نامشخص';
        const jobCity = req.job && req.job.city ? req.job.city.name : 'نامشخص';
        const appliedDate = new Date(req.applied_at).toLocaleDateString('fa-IR');
        const statusClass = req.status === "Accepted" ? "status-approved" : req.status === "Pending" ? "status-pending" : "status-rejected";

        return `
            <div class="card">
                <h3>درخواست شغل برای: ${jobTitle} در ${jobCity}</h3>
                <p><strong>کارجو:</strong> ${userName} (${req.user?.username || 'نامشخص'})</p>
                <p><strong>شناسه درخواست:</strong> ${req.id}</p>
                <p><strong>تاریخ درخواست:</strong> ${appliedDate}</p>
                <p><strong>وضعیت:</strong> <span class="${statusClass}">${req.status}</span></p>
            </div>
        `;
    }).join('');
    console.log("User job applications rendered.");
}

/**
 * تابع اصلی برای دریافت و نمایش داده‌ها بر اساس نوع درخواستی.
 * حالا این تابع بسته به نوع، یا از allJobsData استفاده می‌کنه یا مستقیماً از API درخواست می‌ده.
 */
async function fetchAndRenderData(type) {
    currentView = type;
    showSystemMessage('⏳ در حال بارگذاری...');
    console.log(`Changing view to: ${currentView}`);
    try {
        if (type === 'city') {
            const data = await fetchDataNonJob(type);
            renderCities(data);
        } else if (type === 'user') {
            const data = await fetchDataNonJob(type);
            renderUsers(data);
        } else if (type === 'job') {
            renderJobs(false);
        } else if (type === 'pending_jobs') {
            renderJobs(true);
        } else if (type === 'user_job_applications') {
            const data = await fetchDataNonJob(type);
            renderUserJobApplications(data);
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

// تابع جدید برای دریافت داده‌های غیر شغل (شهرها، کاربران، درخواست‌های شغلی)
async function fetchDataNonJob(type) {
    console.log(`Fetching non-job data for type: ${type}`);
    let endpoint = '';
    let requiresAuth = true;

    switch(type) {
        case 'city':
            endpoint = 'cities';
            requiresAuth = false;
            break;
        case 'user':
            endpoint = 'admin/users';
            break;
        case 'user_job_applications':
            endpoint = 'admin/user-jobs';
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


// تابعی برای فراخوانی اولیه و همچنین رفرش کلی شغل‌ها
async function fetchAllJobsAndRender(viewToSwitchTo) {
    showSystemMessage('⏳ در حال بارگذاری تمام شغل‌ها...');
    try {
        await fetchAllJobs();
        fetchAndRenderData(viewToSwitchTo);
    } catch (error) {
        showSystemMessage(`❌ خطا در بارگذاری شغل‌ها: ${error.message}`, true);
    }
}

// توابع رویدادهای کلیک برای دکمه‌های بالای صفحه
function showData(type) {
    if (type === 'job' || type === 'pending_jobs') {
        fetchAllJobsAndRender(type);
    } else {
        fetchAndRenderData(type);
    }
}


// --- توابع عملیات (تأیید، حذف) ---

async function updateJobStatus(jobId, isApproved) {
    try {
        console.log(`Attempting to update job ${jobId} to is_approved: ${isApproved}`);
        const response = await fetch(`${BASE_URL}/admin/jobs/${jobId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ is_approved: isApproved })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `خطا در به‌روزرسانی وضعیت شغل ${jobId}.`);
        }

        alert(`✅ شغل ${jobId} با موفقیت ${isApproved ? 'تأیید' : 'رد'} شد!`);
        console.log(`Job ${jobId} updated successfully. Now updating local data and refreshing view.`);
        const updatedJobIndex = allJobsData.findIndex(job => job.id === jobId);
        if (updatedJobIndex !== -1) {
            allJobsData[updatedJobIndex].is_approved = isApproved;
        }

        if (isApproved) {
            fetchAndRenderData('job');
        } else {
            fetchAndRenderData(currentView);
        }
        
    } catch (error) {
        console.error("Error updating job status:", error);
        alert("❌ خطا: " + error.message);
    }
}

async function deleteJob(jobId, viewToRefresh) {
    if (!confirm("آیا از حذف این شغل اطمینان دارید؟")) {
        return;
    }
    try {
        console.log(`Attempting to delete job ${jobId}.`);
        const response = await fetch(`${BASE_URL}/admin/jobs/${jobId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `خطا در حذف شغل ${jobId}.`);
        }

        alert(`✅ شغل ${jobId} با موفقیت حذف شد!`);
        console.log(`Job ${jobId} deleted successfully. Now updating local data and refreshing view.`);
        allJobsData = allJobsData.filter(job => job.id !== jobId);
        fetchAndRenderData(viewToRefresh);
    } catch (error) {
        console.error("Error deleting job:", error);
        alert("❌ خطا: " + error.message);
    }
}