// frontend/js/job.js

document.addEventListener("DOMContentLoaded", async () => {
  const jobDetails = document.getElementById("job-details");
  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get("id");

  if (!jobId) {
    jobDetails.innerHTML = "<p class='system-msg'>❌ شناسه شغل نامعتبر است.</p>";
    return;
  }

  try {
    const response = await fetch(`http://localhost:8000/v1/jobs/${jobId}`);
    if (!response.ok) {
        if (response.status === 404) {
            jobDetails.innerHTML = "<p class='system-msg'>❌ شغل یافت نشد یا هنوز تأیید نشده است.</p>";
            return;
        }
        throw new Error("خطا در دریافت اطلاعات شغل");
    }

    const job = await response.json();

    const title = job.title || "عنوان نامشخص";
    const description = job.description || "توضیحاتی موجود نیست";
    const cityName = job.city?.name || "شهر نامشخص";
    const employerInfo = job.employer_info?.trim() ? job.employer_info : "اطلاعاتی ثبت نشده";

    const employerId = job.employer?.id || null;
    const token = localStorage.getItem("access_token");
    const user = JSON.parse(localStorage.getItem("user"));
    const isCurrentUserEmployer = user?.is_employer;

    let actionButtonsHTML = "";

    // اگر کاربر لاگین کرده باشد
    if (token && user) {
        // اگر کارجو باشد و این شغل متعلق به خودش نباشد
        if (!isCurrentUserEmployer || (isCurrentUserEmployer && user.id !== employerId)) {
             // دکمه درخواست شغل
            actionButtonsHTML += `
                <button class="apply-button" id="applyJobBtn">درخواست برای این شغل</button>
            `;
            // دکمه چت با کارفرما
            if (employerId) {
                actionButtonsHTML += `
                    <button class="chat-button" onclick="goToChatWithEmployer(${jobId})">
                        شروع چت با کارفرما
                    </button>
                `;
            } else {
                actionButtonsHTML += `<p class="message-info" style="color: grey;">اطلاعات کارفرما برای چت موجود نیست.</p>`;
            }
        } else if (isCurrentUserEmployer && user.id === employerId) {
            // اگر کارفرما باشد و این شغل متعلق به خودش باشد، دکمه‌های خاصی ندارد یا می‌تواند به داشبوردش برگردد
            actionButtonsHTML += `<p class="message-info">این شغل توسط شما ثبت شده است.</p>`;
            actionButtonsHTML += `<a href="employer_dashboard.html" class="apply-button" style="background-color: #5cb85c;">بازگشت به داشبورد</a>`;
        }
    } else {
        // اگر لاگین نکرده باشد، این حالت دیگر نباید رخ دهد اگر کاربر از طریق main.js هدایت شده باشد.
        // اما برای اطمینان و جلوگیری از خطای احتمالی، آن را نگه می‌داریم و پیام می‌دهد باید لاگین کند.
        actionButtonsHTML += `
            <p class="message-info">برای درخواست شغل یا چت با کارفرما باید وارد حساب کاربری خود شوید.</p>
            <a href="login.html" class="chat-button" style="background-color: #6c757d;">ورود/ثبت‌نام</a>
        `;
    }

    jobDetails.innerHTML = `
      <h2>${title}</h2>
      <p><strong>شهر:</strong> ${cityName}</p>
      <p><strong>توضیحات:</strong> ${description}</p>
      <h3>اطلاعات کارفرما:</h3>
      <p><strong>راه ارتباطی:</strong> ${employerInfo}</p>
      <div class="job-actions-container">
        ${actionButtonsHTML}
      </div>
    `;

    const applyJobBtn = document.getElementById("applyJobBtn");
    if (applyJobBtn) {
        applyJobBtn.addEventListener("click", async () => {
            const confirmApply = confirm("آیا از درخواست برای این شغل اطمینان دارید؟");
            if (!confirmApply) return;

            try {
                const applyResponse = await fetch("http://localhost:8000/v1/user/jobs", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ job_id: parseInt(jobId) })
                });

                if (!applyResponse.ok) {
                    const errorData = await applyResponse.json();
                    throw new Error(errorData.detail || "خطا در ثبت درخواست شغل.");
                }

                alert("✅ درخواست شغل با موفقیت ثبت شد!");
                applyJobBtn.disabled = true; // disable button after applying
                applyJobBtn.textContent = "درخواست شما ثبت شد";
            } catch (error) {
                alert("❌ خطا در ثبت درخواست شغل: " + error.message);
                console.error("Apply job error:", error);
            }
        });
    }

  } catch (error) {
    jobDetails.innerHTML = `<p class='system-msg'>❌ خطا در بارگذاری اطلاعات شغل: ${error.message}</p>`;
    console.error("Job details error:", error);
  }
});

// Helper function to go to chat page
function goToChatWithEmployer(jobId) {
    localStorage.setItem("job_id", jobId); // Store jobId for chat.js to pick up
    window.location.href = "chat.html";
}