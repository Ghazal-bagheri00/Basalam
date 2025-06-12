// frontend/js/my_applications.js

document.addEventListener("DOMContentLoaded", () => {
    initMyApplications();
});

async function initMyApplications() {
    const myApplicationsList = document.getElementById("my-applications-list");
    const token = localStorage.getItem('access_token');
    const user = JSON.parse(localStorage.getItem('user'));

    if (!token || !user) {
        displayMessage(myApplicationsList, "❌ برای مشاهده درخواست‌ها، لطفاً وارد شوید.", true);
        setTimeout(() => window.location.href = "login.html", 2000);
        return;
    }

    try {
        const applications = await fetchApplications(token);
        renderApplications(myApplicationsList, applications);
    } catch (error) {
        console.error("خطا در دریافت درخواست‌ها:", error);
        displayMessage(myApplicationsList, `❌ خطا در بارگذاری درخواست‌های شغلی: ${error.message}`, true);
    }
}

async function fetchApplications(token) {
    const response = await fetch("http://localhost:8000/v1/user/my-jobs", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "خطای ناشناس در دریافت درخواست‌ها");
    }

    return response.json();
}

function renderApplications(container, applications) {
    container.innerHTML = ""; // Clear previous content

    if (!applications.length) {
        displayMessage(container, "شما تا کنون برای هیچ شغلی درخواست نداده‌اید.");
        return;
    }

    applications.forEach(app => container.appendChild(createApplicationCard(app)));
}

function createApplicationCard(app) {
    const job = app.job || {};
    const employer = job.employer || {};
    const city = job.city || {};

    const jobTitle = job.title || "نامشخص";
    const cityName = city.name || "نامشخص";
    const employerName = `${employer.first_name || ''} ${employer.last_name || ''}`.trim() || "نامشخص";
    const applicantNotes = app.applicant_notes || "ندارد";
    const appliedDate = formatDate(app.applied_at);
    const approvedDate = app.employer_approved_at ? formatDate(app.employer_approved_at) : "در انتظار";

    const { statusText, statusClass } = mapStatus(app.status);

    const card = document.createElement("div");
    card.className = "application-card";
    card.innerHTML = `
        <h4>شغل: ${jobTitle}</h4>
        <p><strong>کارفرما:</strong> ${employerName}</p>
        <p><strong>شهر:</strong> ${cityName}</p>
        <p><strong>توضیحات شما:</strong> ${applicantNotes}</p>
        <p><strong>تاریخ درخواست:</strong> ${appliedDate}</p>
        <p><strong>وضعیت:</strong> <span class="${statusClass}">${statusText}</span></p>
        ${app.status === "Accepted" ? `<p><strong>تاریخ پذیرش:</strong> ${approvedDate}</p>` : ""}
        <p><a href="job.html?id=${app.job_id}">مشاهده جزئیات شغل</a></p>
    `;
    return card;
}

function displayMessage(container, message, isError = false) {
    container.innerHTML = `<p class="no-applications system-msg ${isError ? 'error' : ''}">${message}</p>`;
}

function mapStatus(status) {
    switch (status) {
        case "Accepted":
            return { statusText: "پذیرفته شده", statusClass: "status-approved" };
        case "Pending":
            return { statusText: "در انتظار", statusClass: "status-pending" };
        case "Rejected":
        default:
            return { statusText: "رد شده", statusClass: "status-rejected" };
    }
}

function formatDate(dateString) {
    try {
        return new Date(dateString).toLocaleDateString('fa-IR');
    } catch {
        return "نامشخص";
    }
}
