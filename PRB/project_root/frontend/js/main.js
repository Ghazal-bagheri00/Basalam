// frontend/js/main.js

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

    jobs.forEach(job => {
      const jobBox = document.createElement("div");
      jobBox.className = "job-card";

      jobBox.innerHTML = `
        <h3>${job.title}</h3>
        <p><strong>شهر:</strong> ${job.city?.name || "نامشخص"}</p>
        <p><strong>توضیحات:</strong> ${job.description.substring(0, 150)}...</p>
        <button class="view-details-button" onclick="goToLoginPageAndRedirect(${job.id})">
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

// ✅ تابع جدید: هدایت به صفحه ورود و سپس به صفحه جزئیات شغل
function goToLoginPageAndRedirect(jobId) {
  // ذخیره jobId در localStorage
  localStorage.setItem("redirect_job_id", jobId);
  // هدایت کاربر به صفحه ورود
  window.location.href = `login.html`;
}