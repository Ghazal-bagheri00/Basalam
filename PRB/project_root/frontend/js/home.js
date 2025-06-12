// frontend/js/home.js

document.addEventListener("DOMContentLoaded", async () => {
  const jobContainer = document.getElementById("jobs");
  jobContainer.innerHTML = "<p class='system-msg'>در حال بارگذاری شغل‌ها...</p>";

  try {
    const response = await fetch("http://localhost:8000/v1/jobs");
    if (!response.ok) {
      throw new Error("خطا در دریافت شغل‌ها");
    }
    const jobs = await response.json();

    jobContainer.innerHTML = "";

    if (jobs.length === 0) {
      jobContainer.innerHTML = "<p class='system-msg'>در حال حاضر هیچ شغل تأیید شده‌ای وجود ندارد.</p>";
      return;
    }

    const token = localStorage.getItem('access_token'); // بررسی می‌کنیم که کاربر لاگین است یا نه

    jobs.forEach(job => {
      const jobBox = document.createElement("div");
      jobBox.className = "job-card";

      // ✅ تغییر در اینجا: اگر کاربر لاگین است، مستقیم به job.html می‌رود، در غیر این صورت به login.html (که بعداً به job.html هدایت می‌کند)
      const detailsAction = token ? `goToJobDetailsPage(${job.id})` : `goToLoginPageAndRedirect(${job.id})`;

      jobBox.innerHTML = `
        <h3>${job.title}</h3>
        <p><strong>شهر:</strong> ${job.city?.name || "نامشخص"}</p>
        <p><strong>توضیحات:</strong> ${job.description.substring(0, 150)}...</p>
        <button class="view-details-button" onclick="${detailsAction}">
          مشاهده جزئیات
        </button>
      `;
      jobContainer.appendChild(jobBox);
    });
  } catch (error) {
    jobContainer.innerHTML = `<p class='system-msg'>❌ خطا در دریافت اطلاعات شغل‌ها! لطفاً بعداً تلاش کنید.</p>`;
    console.error("Job load error:", error);
  }
});

// تابع جدید: هدایت مستقیم به صفحه جزئیات شغل (برای کاربران لاگین شده)
function goToJobDetailsPage(jobId) {
    window.location.href = `job.html?id=${jobId}`;
}

// تابع فعلی: هدایت به صفحه ورود و سپس به صفحه جزئیات شغل (برای کاربران لاگین نشده)
function goToLoginPageAndRedirect(jobId) {
  localStorage.setItem("redirect_job_id", jobId);
  window.location.href = `login.html`;
}


// ✅ تغییرات در بخش "درخواست‌های من" (بدون تغییرات عملکردی در این بخش، فقط قرارگیری کد)
document.addEventListener("DOMContentLoaded", () => {
    const logoutBtn = document.getElementById("logoutBtn");
    const myProfileBtn = document.getElementById("myProfileBtn");
    const myApplicationsBtn = document.getElementById("myApplicationsBtn");

    if (logoutBtn) { // Add null check for elements that might not exist on all pages where this JS is loaded
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            localStorage.removeItem('user');
            window.location.href = 'index.html';
        });
    }
    if (myProfileBtn) {
        myProfileBtn.addEventListener("click", () => {
            // این خط را حذف یا کامنت کنید:
            // alert("پروفایل من (در دست ساخت)");
            window.location.href = "profile.html"; // این خط فعال باقی بماند
        });
    }
    if (myApplicationsBtn) {
        myApplicationsBtn.addEventListener("click", async () => {
            const token = localStorage.getItem('access_token');
            if (!token) {
                alert("لطفاً ابتدا وارد شوید.");
                window.location.href = "login.html";
                return;
            }

            try {
                const response = await fetch("http://localhost:8000/v1/user/my-jobs", {
                    headers: {
                        "Authorization": `Bearer ${token}`
                    }
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "خطا در دریافت درخواست‌های شغلی شما.");
                }
                const applications = await response.json();
                let msg = "درخواست‌های شغلی شما:\n\n";
                if (applications.length === 0) {
                    msg += "شما تا کنون برای هیچ شغلی درخواست نداده‌اید.";
                } else {
                    applications.forEach(app => {
                        const jobTitle = app.job?.title || "نامشخص";
                        const statusText = app.status === "Pending" ? "در انتظار" : app.status === "Accepted" ? "پذیرفته شده" : "رد شده";
                        msg += `- شغل: ${jobTitle} (وضعیت: ${statusText})\n`;
                    });
                }
                alert(msg);
            } catch (error) {
                alert("❌ خطا در بارگذاری درخواست‌های شغلی: " + error.message);
                console.error("Error fetching user applications:", error);
            }
        });
    }
});