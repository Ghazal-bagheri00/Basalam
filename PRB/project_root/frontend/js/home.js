document.addEventListener("DOMContentLoaded", async () => {
  const jobContainer = document.getElementById("jobs");
  jobContainer.innerHTML = "<p>در حال بارگذاری شغل‌ها...</p>";

  try {
    const response = await fetch("http://localhost:8000/v1/jobs");
    if (!response.ok) {
      throw new Error("خطا در دریافت شغل‌ها");
    }

    const jobs = await response.json();
    jobContainer.innerHTML = ""; 

    jobs.forEach(job => {
      const jobBox = document.createElement("div");
      jobBox.className = "job-card";

      jobBox.innerHTML = `
        <h3>${job.title}</h3>
        <p><strong>شهر:</strong> ${job.city?.name || "نامشخص"}</p>
        <p><strong>توضیحات:</strong> ${job.description}</p>
        <button class="apply-button" onclick="goToChat(${job.id})">
          مشاهده جزئیات
        </button>
      `;

      jobContainer.appendChild(jobBox);
    });
  } catch (error) {
    jobContainer.innerHTML = `<p>خطا در دریافت اطلاعات شغل‌ها!</p>`;
    console.error("Job load error:", error);
  }
});

// ✅ تابع هدایت به صفحه چت با ذخیره‌سازی job_id
function goToChat(jobId) {
  localStorage.setItem("job_id", jobId);
  window.location.href = "chat.html";
}

  