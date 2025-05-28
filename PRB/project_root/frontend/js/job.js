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
      const employerName = job.employer ? `${job.employer.first_name} ${job.employer.last_name}` : "نامشخص"; // ✅ جدید: نام کارفرما
  
      const employerId = job.employer?.id || null;
      const token = localStorage.getItem("access_token");
      const user = JSON.parse(localStorage.getItem("user"));
      const isCurrentUserEmployer = user?.is_employer;
      const currentUserId = user?.id;
  
      let actionButtonsHTML = "";
      let hasApplied = false;
      let applicationStatus = "";
  
      // بررسی اینکه آیا کاربر قبلا برای این شغل درخواست داده است (فقط برای کارجو)
      if (token && user && !isCurrentUserEmployer) {
          try {
              const userApplicationsResponse = await fetch(`http://localhost:8000/v1/user/my-jobs`, {
                  headers: { "Authorization": `Bearer ${token}` }
              });
              if (userApplicationsResponse.ok) {
                  const applications = await userApplicationsResponse.json();
                  const existingApp = applications.find(app => app.job_id === parseInt(jobId));
                  if (existingApp) {
                      hasApplied = true;
                      applicationStatus = existingApp.status;
                  }
              }
          } catch (error) {
              console.error("Error checking existing application:", error);
          }
      }
  
  
      // اگر کاربر لاگین کرده باشد
      if (token && user) {
          // اگر کارجو باشد
          if (!isCurrentUserEmployer) {
               // دکمه درخواست شغل
              if (hasApplied) {
                  actionButtonsHTML += `
                      <p class="message-info">وضعیت درخواست شما: <span class="status-${applicationStatus.toLowerCase()}">${applicationStatus === "Pending" ? "در انتظار" : applicationStatus === "Accepted" ? "پذیرفته شده" : "رد شده"}</span></p>
                      <button class="apply-button" disabled style="background-color: #6c757d;">${applicationStatus === "Accepted" ? "شما پذیرفته شده‌اید!" : applicationStatus === "Rejected" ? "درخواست شما رد شد." : "شما قبلاً درخواست داده‌اید"}</button>
                  `;
              } else {
                  // ✅ اضافه شد: فیلد توضیحات و دکمه درخواست
                  actionButtonsHTML += `
                      <div class="form-group" style="margin-top: 20px;">
                          <label for="applicant_notes">توضیحات شما برای کارفرما (اختیاری):</label>
                          <textarea id="applicant_notes" rows="4" placeholder="در اینجا می‌توانید مهارت‌ها، تجربیات مرتبط یا هر نکته دیگری را که می‌خواهید کارفرما بداند، بیان کنید."></textarea>
                      </div>
                      <button class="apply-button" id="applyJobBtn">درخواست برای این شغل</button>
                  `;
              }
              // دکمه چت با کارفرما
              if (employerId && currentUserId !== employerId) {
                  actionButtonsHTML += `
                      <button class="chat-button" onclick="goToChatWithEmployer(${jobId})">
                          شروع چت با کارفرما
                      </button>
                  `;
              } else if (employerId === currentUserId) {
                  actionButtonsHTML += `<p class="message-info">این شغل توسط شما ثبت شده است.</p>`;
              } else {
                  actionButtonsHTML += `<p class="message-info" style="color: grey;">اطلاعات کارفرما برای چت موجود نیست.</p>`;
              }
          } else if (isCurrentUserEmployer && user.id === employerId) {
              // اگر کارفرما باشد و این شغل متعلق به خودش باشد
              actionButtonsHTML += `<p class="message-info">این شغل توسط شما ثبت شده است.</p>`;
              actionButtonsHTML += `<a href="employer_dashboard.html" class="apply-button" style="background-color: #5cb85c;">بازگشت به داشبورد</a>`;
          } else if (isCurrentUserEmployer && user.id !== employerId) {
              // اگر کارفرما باشد اما این شغل متعلق به کارفرمای دیگری باشد
              actionButtonsHTML += `<p class="message-info">شما به عنوان کارفرما نمی‌توانید برای این شغل درخواست دهید.</p>`;
          }
      } else {
          // ✅ تغییر در اینجا: اگر لاگین نکرده باشد، دکمه "درخواست برای این شغل" او را به صفحه ورود هدایت می‌کند و job_id را ذخیره می‌کند.
          actionButtonsHTML += `
              <p class="message-info">برای درخواست شغل یا چت با کارفرما باید وارد حساب کاربری خود شوید.</p>
              <button class="chat-button" onclick="redirectToLoginForJob(${jobId})" style="background-color: #6c757d;">ورود/ثبت‌نام برای درخواست</button>
          `;
      }
  
      jobDetails.innerHTML = `
        <h2>${title}</h2>
        <p><strong>شهر:</strong> ${cityName}</p>
        <p><strong>توضیحات:</strong> ${description}</p>
        <h3>اطلاعات کارفرما:</h3>
        <p><strong>نام کارفرما:</strong> ${employerName}</p> <p><strong>راه ارتباطی:</strong> ${employerInfo}</p>
        <div class="job-actions-container">
          ${actionButtonsHTML}
        </div>
      `;
  
      const applyJobBtn = document.getElementById("applyJobBtn");
      if (applyJobBtn) {
          applyJobBtn.addEventListener("click", async () => {
              const confirmApply = confirm("آیا از درخواست برای این شغل اطمینان دارید؟");
              if (!confirmApply) return;
  
              const applicantNotes = document.getElementById("applicant_notes") ? document.getElementById("applicant_notes").value.trim() : null; // ✅ دریافت توضیحات
  
              try {
                  const applyResponse = await fetch("http://localhost:8000/v1/user/jobs", {
                      method: "POST",
                      headers: {
                          "Content-Type": "application/json",
                          "Authorization": `Bearer ${token}`
                      },
                      body: JSON.stringify({ job_id: parseInt(jobId), applicant_notes: applicantNotes }) // ✅ ارسال توضیحات
                  });
  
                  if (!applyResponse.ok) {
                      const errorData = await applyResponse.json();
                      throw new Error(errorData.detail || "خطا در ثبت درخواست شغل.");
                  }
  
                  alert("✅ درخواست شغل با موفقیت ثبت شد و در انتظار بررسی کارفرماست!");
                  applyJobBtn.disabled = true; // disable button after applying
                  applyJobBtn.textContent = "درخواست شما ثبت شد (در انتظار)";
                  const statusInfo = document.createElement('p');
                  statusInfo.className = 'message-info';
                  statusInfo.innerHTML = `وضعیت درخواست شما: <span class="status-pending">در انتظار</span>`;
                  applyJobBtn.parentNode.insertBefore(statusInfo, applyJobBtn);
                  // حذف فیلد توضیحات پس از ارسال موفق
                  const notesField = document.getElementById("applicant_notes");
                  if (notesField && notesField.parentNode) {
                      notesField.parentNode.style.display = 'none'; // یا notesField.parentNode.remove();
                  }
                  applyJobBtn.remove();
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
      localStorage.setItem("job_id", jobId);
      window.location.href = "chat.html";
  }
  
  // ✅ جدید: تابع برای هدایت به صفحه ورود و ذخیره job_id برای ریدایرکت پس از ورود
  function redirectToLoginForJob(jobId) {
      localStorage.setItem("redirect_job_id", jobId);
      window.location.href = `login.html`;
  }