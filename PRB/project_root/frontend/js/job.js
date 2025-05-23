document.addEventListener("DOMContentLoaded", async () => {
  const jobDetails = document.getElementById("job-details");
  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get("id");

  if (!jobId) {
    jobDetails.innerHTML = "<p>❌ شناسه شغل نامعتبر است.</p>";
    return;
  }

  try {
    const response = await fetch(`http://localhost:8000/v1/jobs/${jobId}`);
    if (!response.ok) throw new Error("خطا در دریافت اطلاعات شغل");

    const job = await response.json();

    const title = job.title || "عنوان نامشخص";
    const description = job.description || "توضیحاتی موجود نیست";
    const cityName = job.city?.name || "شهر نامشخص";
    const employerInfo = job.employer_info?.trim()
      ? job.employer_info
      : "اطلاعاتی ثبت نشده";

    const employerId = job.employer?.id || job.employer_id || null;

    // بررسی ورود کاربر از روی وجود توکن در localStorage
    const token = localStorage.getItem("access_token");

    let chatButtonHTML = "";
    if (employerId && token) {
      localStorage.setItem("employer_id", employerId);
      localStorage.setItem("job", JSON.stringify(job));
      chatButtonHTML = `
        <button onclick="window.location.href='chat.html'" style="
          margin-top: 20px;
          padding: 10px 20px;
          background-color: #7b4dff;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;">
          شروع چت با کارفرما
        </button>
      `;
    } else if (employerId && !token) {
      chatButtonHTML = `
        <p style="color: red; margin-top: 20px;">
          برای شروع چت با کارفرما باید ابتدا وارد حساب کاربری خود شوید.
        </p>
      `;
    }

    jobDetails.innerHTML = `
      <h2>${title}</h2>
      <p><strong>شهر:</strong> ${cityName}</p>
      <p><strong>توضیحات:</strong> ${description}</p>
      <h3>اطلاعات کارفرما:</h3>
      <p><strong>راه ارتباطی:</strong> ${employerInfo}</p>
      ${chatButtonHTML}
    `;
  } catch (error) {
    jobDetails.innerHTML = "<p>❌ خطا در بارگذاری اطلاعات شغل.</p>";
    console.error("Job details error:", error);
  }
});
