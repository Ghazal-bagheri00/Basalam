document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");
    const user = JSON.parse(localStorage.getItem('user'));

    if (!token || !user || !user.is_employer) {
        alert("❌ فقط کارفرمایان مجاز به دسترسی به این داشبورد هستند. لطفاً وارد حساب کارفرمایی خود شوید.");
        window.location.href = "login.html";
        return;
    }

    // Display user's first name
    // const userNameDisplay = document.getElementById("userNameDisplay");
    // if (userNameDisplay) {
    //     userNameDisplay.textContent = user.first_name || "کاربر";
    // }

    const viewMyJobsBtn = document.getElementById("viewMyJobsBtn");
    const myJobsSection = document.getElementById("my-jobs-section");
    const myJobsList = document.getElementById("my-jobs-list");

    viewMyJobsBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        // Toggle visibility
        if (myJobsSection.style.display === "none" || myJobsSection.style.display === "") {
            myJobsSection.style.display = "block";
            myJobsList.innerHTML = "<p class='system-msg'>در حال بارگذاری شغل‌های شما...</p>";
            await fetchMyJobs();
        } else {
            myJobsSection.style.display = "none";
        }
    });

    async function fetchMyJobs() {
        try {
            const response = await fetch("http://localhost:8000/v1/employer/my-jobs", {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "خطا در دریافت شغل‌های کارفرما.");
            }

            const jobs = await response.json();
            myJobsList.innerHTML = "";

            if (jobs.length === 0) {
                myJobsList.innerHTML = "<p class='system-msg'>شما هنوز هیچ شغلی ثبت نکرده‌اید.</p>";
                return;
            }

            jobs.forEach(job => {
                const jobCard = document.createElement("div");
                jobCard.className = "job-card";
                jobCard.innerHTML = `
                    <h4>${job.title}</h4>
                    <p><strong>شهر:</strong> ${job.city?.name || "نامشخص"}</p>
                    <p><strong>توضیحات:</strong> ${job.description.substring(0, 100)}...</p>
                    <p><strong>وضعیت:</strong> <span class="job-status status-${job.is_approved ? 'approved' : 'pending'}">${job.is_approved ? 'تأیید شده' : 'در انتظار تأیید'}</span></p>
                    <p><a href="job.html?id=${job.id}">مشاهده جزئیات</a></p>
                `;
                myJobsList.appendChild(jobCard);
            });

        } catch (error) {
            console.error("Error fetching employer jobs:", error);
            myJobsList.innerHTML = `<p class='system-msg'>❌ خطا: ${error.message}</p>`;
        }
    }
});