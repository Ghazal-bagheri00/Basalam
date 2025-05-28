// frontend/js/employer_dashboard.js

document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");
    const user = JSON.parse(localStorage.getItem('user'));

    // بررسی احراز هویت
    if (!token || !user || !user.is_employer) {
        alert("❌ فقط کارفرمایان مجاز به دسترسی به این داشبورد هستند. لطفاً وارد حساب کارفرمایی خود شوید.");
        window.location.href = "login.html";
        return;
    }

    // عناصر HTML
    const tabButtons = document.querySelectorAll('.dashboard-nav-tab');
    const sections = document.querySelectorAll('.dashboard-content-section');
    const myJobsList = document.getElementById("my-jobs-list");
    const jobApplicationsList = document.getElementById("job-applications-list");
    const acceptedEmployeesList = document.getElementById("accepted-employees-list"); // ✅ جدید
    const chatContactsList = document.getElementById("chat-contacts-list");

    // تابع برای تغییر تب
    function activateTab(tabName) {
        // حذف کلاس active از همه دکمه‌های تب و بخش‌های محتوا
        tabButtons.forEach(button => button.classList.remove('active'));
        sections.forEach(section => section.classList.remove('active'));

        // اضافه کردن کلاس active به دکمه تب و بخش محتوای مربوطه
        document.querySelector(`.dashboard-nav-tab[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-section`).classList.add('active');

        // بارگذاری محتوای تب فعال (اگر قبلاً بارگذاری نشده)
        switch (tabName) {
            case 'my-jobs':
                fetchMyJobs();
                break;
            case 'job-applications':
                fetchJobApplications();
                break;
            case 'accepted-employees': // ✅ جدید
                fetchAcceptedEmployees();
                break;
            case 'chat-contacts':
                fetchChatContacts();
                break;
        }
    }

    // اضافه کردن شنونده رویداد برای دکمه‌های تب
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            activateTab(button.dataset.tab);
        });
    });

    // بارگذاری محتوای اولین تب به صورت پیش‌فرض
    activateTab('my-jobs');

    // --- توابع واکشی و نمایش داده‌ها ---

    async function fetchMyJobs() {
        myJobsList.innerHTML = "<p class='system-msg'>در حال بارگذاری شغل‌های شما...</p>";
        try {
            const response = await fetch("http://localhost:8000/v1/employer/my-jobs", {
                headers: { "Authorization": `Bearer ${token}` }
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
                
                // ✅ نمایش جزئیات کامل‌تر شغل
                jobCard.innerHTML = `
                    <h4>${job.title}</h4>
                    <p><strong>شناسه شغل:</strong> ${job.id}</p>
                    <p><strong>شهر:</strong> ${job.city?.name || "نامشخص"}</p>
                    <p><strong>توضیحات:</strong> ${job.description}</p> <p><strong>اطلاعات کارفرما:</strong> ${job.employer_info || "ثبت نشده"}</p>
                    <p><strong>وضعیت:</strong> <span class="job-status status-${job.is_approved ? 'approved' : 'pending'}">${job.is_approved ? 'تأیید شده' : 'در انتظار تأیید'}</span></p>
                    <p><a href="job.html?id=${job.id}">مشاهده صفحه عمومی شغل</a></p>
                `;
                myJobsList.appendChild(jobCard);
            });
        } catch (error) {
            console.error("Error fetching employer jobs:", error);
            myJobsList.innerHTML = `<p class='system-msg'>❌ خطا: ${error.message}</p>`;
        }
    }

    async function fetchJobApplications() {
        jobApplicationsList.innerHTML = "<p class='system-msg'>در حال بارگذاری درخواست‌های شغلی...</p>";
        try {
            const response = await fetch("http://localhost:8000/v1/employer/job-applications", {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "خطا در دریافت درخواست‌های شغلی.");
            }

            const applications = await response.json();
            jobApplicationsList.innerHTML = "";

            if (applications.length === 0) {
                jobApplicationsList.innerHTML = "<p class='system-msg'>هیچ درخواست شغلی جدیدی برای شغل‌های شما وجود ندارد.</p>";
                return;
            }

            applications.forEach(app => {
                const applicationCard = document.createElement("div");
                applicationCard.className = "application-card";
                
                const statusClass = app.status === "Accepted" ? "status-approved" : app.status === "Pending" ? "status-pending" : "status-rejected";
                const appliedDate = new Date(app.applied_at).toLocaleDateString('fa-IR');
                const approvedDate = app.employer_approved_at ? new Date(app.employer_approved_at).toLocaleDateString('fa-IR') : 'نامشخص';

                applicationCard.innerHTML = `
                    <h4>درخواست از ${app.user.first_name} ${app.user.last_name}</h4>
                    <p><strong>برای شغل:</strong> ${app.job.title} (${app.job.city.name})</p>
                    <p><strong>تاریخ درخواست:</strong> ${appliedDate}</p>
                    <p><strong>توضیحات کارجو:</strong> ${app.applicant_notes || "ندارد"}</p> <p><strong>وضعیت:</strong> <span class="${statusClass}">${app.status === "Pending" ? "در انتظار" : app.status === "Accepted" ? "پذیرفته شده" : "رد شده"}</span></p>
                    ${app.status === "Accepted" ? `<p><strong>تاریخ پذیرش:</strong> ${approvedDate}</p>` : ''}
                    <p><strong>تماس با کارجو:</strong> ${app.user.username}</p>
                    <div class="application-actions">
                        ${app.status === "Pending" ? `
                            <button class="approve-btn" data-id="${app.id}">پذیرش</button>
                            <button class="reject-btn" data-id="${app.id}">رد</button>
                        ` : ''}
                        ${app.status !== "Rejected" ? ` <button class="chat-with-applicant-btn" data-user-id="${app.user.id}">چت با کارجو</button>
                        ` : ''}
                    </div>
                `;
                jobApplicationsList.appendChild(applicationCard);
            });

            // افزودن شنونده رویداد برای دکمه‌های پذیرش و رد
            document.querySelectorAll('.approve-btn').forEach(button => {
                button.addEventListener('click', (e) => updateApplicationStatus(e.target.dataset.id, 'Accepted'));
            });
            document.querySelectorAll('.reject-btn').forEach(button => {
                button.addEventListener('click', (e) => updateApplicationStatus(e.target.dataset.id, 'Rejected'));
            });
            // افزودن شنونده رویداد برای دکمه چت با کارجو
            document.querySelectorAll('.chat-with-applicant-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    const applicantId = e.target.dataset.userId;
                    localStorage.setItem("employer_chat_user_id", applicantId);
                    window.location.href = "chat.html";
                });
            });

        } catch (error) {
            console.error("Error fetching job applications:", error);
            jobApplicationsList.innerHTML = `<p class='system-msg'>❌ خطا: ${error.message}</p>`;
        }
    }

    async function updateApplicationStatus(applicationId, status) {
        if (!confirm(`آیا از تغییر وضعیت این درخواست به "${status === 'Accepted' ? 'پذیرفته شده' : 'رد شده'}" اطمینان دارید؟`)) {
            return;
        }

        try {
            const response = await fetch(`http://localhost:8000/v1/employer/job-applications/${applicationId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ status: status })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `خطا در به‌روزرسانی وضعیت درخواست ${applicationId}.`);
            }

            alert(`✅ وضعیت درخواست با موفقیت به "${status === 'Accepted' ? 'پذیرفته شده' : 'رد شده'}" تغییر یافت!`);
            // بعد از تغییر وضعیت، لیست درخواست‌ها و لیست کارکنان پذیرفته شده را رفرش می‌کنیم
            await fetchJobApplications(); 
            await fetchAcceptedEmployees(); // ✅ رفرش لیست کارکنان نیز لازم است
        } catch (error) {
            console.error("Error updating application status:", error);
            alert("❌ خطا: " + error.message);
        }
    }

    // ✅ جدید: تابع واکشی و نمایش کارکنان پذیرفته شده
    async function fetchAcceptedEmployees() {
        acceptedEmployeesList.innerHTML = "<p class='system-msg'>در حال بارگذاری کارکنان پذیرفته شده...</p>";
        try {
            const response = await fetch("http://localhost:8000/v1/employer/accepted-employees", {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "خطا در دریافت لیست کارکنان پذیرفته شده.");
            }

            const employees = await response.json();
            acceptedEmployeesList.innerHTML = "";

            if (employees.length === 0) {
                acceptedEmployeesList.innerHTML = "<p class='system-msg'>هیچ کارمند پذیرفته شده‌ای در لیست شما وجود ندارد.</p>";
                return;
            }

            employees.forEach(emp => {
                const employeeCard = document.createElement("div");
                employeeCard.className = "employee-card";
                
                const appliedDate = new Date(emp.applied_at).toLocaleDateString('fa-IR');
                const approvedDate = new Date(emp.employer_approved_at).toLocaleDateString('fa-IR');

                employeeCard.innerHTML = `
                    <h4>کارمند: ${emp.user.first_name} ${emp.user.last_name}</h4>
                    <p><strong>شناسه کارجو:</strong> ${emp.user.id}</p>
                    <p><strong>شماره تماس:</strong> ${emp.user.username}</p>
                    <p><strong>استان:</strong> ${emp.user.province}</p>
                    <p><strong>پذیرفته شده برای شغل:</strong> ${emp.job.title} (${emp.job.city.name})</p>
                    <p><strong>تاریخ درخواست:</strong> ${appliedDate}</p>
                    <p><strong>تاریخ پذیرش:</strong> ${approvedDate}</p>
                    <p><strong>توضیحات کارجو:</strong> ${emp.applicant_notes || "ندارد"}</p>
                    <div class="employee-actions">
                        <button class="chat-with-applicant-btn" data-user-id="${emp.user.id}">چت با کارمند</button>
                        <button class="remove-employee-btn" data-user-job-id="${emp.id}">حذف از کارکنان</button>
                    </div>
                `;
                acceptedEmployeesList.appendChild(employeeCard);
            });

            // افزودن شنونده رویداد برای دکمه چت با کارمند
            document.querySelectorAll('.employee-actions .chat-with-applicant-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    const applicantId = e.target.dataset.userId;
                    localStorage.setItem("employer_chat_user_id", applicantId);
                    window.location.href = "chat.html";
                });
            });

            // افزودن شنونده رویداد برای دکمه حذف کارمند
            document.querySelectorAll('.employee-actions .remove-employee-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    const userJobIdToRemove = e.target.dataset.userJobId;
                    if (confirm("آیا از حذف این کارمند از لیست کارکنان پذیرفته شده اطمینان دارید؟ این عمل وضعیت درخواست او را به 'رد شده' تغییر می‌دهد.")) {
                        try {
                            const response = await fetch(`http://localhost:8000/v1/employer/accepted-employees/${userJobIdToRemove}/remove`, {
                                method: 'PUT', // از PUT استفاده می‌کنیم تا وضعیت را تغییر دهیم
                                headers: {
                                    'Authorization': `Bearer ${token}`
                                }
                            });
                            if (!response.ok) {
                                const errorData = await response.json();
                                throw new Error(errorData.detail || `خطا در حذف کارمند ${userJobIdToRemove}.`);
                            }
                            alert("✅ کارمند با موفقیت از لیست پذیرفته شده حذف شد!");
                            await fetchAcceptedEmployees(); // رفرش لیست
                            await fetchJobApplications(); // همچنین لیست درخواست ها باید رفرش شود
                        } catch (error) {
                            console.error("Error removing employee:", error);
                            alert("❌ خطا در حذف کارمند: " + error.message);
                        }
                    }
                });
            });

        } catch (error) {
            console.error("Error fetching accepted employees:", error);
            acceptedEmployeesList.innerHTML = `<p class='system-msg'>❌ خطا: ${error.message}</p>`;
        }
    }


    async function fetchChatContacts() {
        chatContactsList.innerHTML = `<p class="system-msg">در حال بارگذاری مخاطبین چت...</p>`;
        try {
            const res = await fetch(`http://localhost:8000/v1/employer/contacts`, {
                method: "GET",
                headers: { "Authorization": `Bearer ${token}` }
            });
            
            if (!res.ok) {
                const errorData = await res.json();
                chatContactsList.innerHTML = `<p class="system-msg">❌ خطا در دریافت مخاطبین: ${errorData.detail || "خطای ناشناخته"}</p>`;
                console.error("Error fetching contacts:", errorData);
                return;
            }
        
            const users = await res.json();
            chatContactsList.innerHTML = "";

            if (!users.length) {
                chatContactsList.innerHTML = `<p class="system-msg">🟡 هنوز پیامی دریافت نکرده‌اید.</p>`;
                return;
            }
        
            users.forEach(user => {
                const div = document.createElement("div");
                div.className = "contact-item";
                div.innerHTML = `
                    <span>${user.first_name} ${user.last_name}</span>
                    <span style="font-size: 0.8em; color: #777;">(${user.username})</span>
                `;
                div.addEventListener("click", () => {
                    localStorage.setItem("employer_chat_user_id", user.id);
                    window.location.href = "chat.html";
                });
                chatContactsList.appendChild(div);
            });
        } catch (err) {
            console.error("Fetch error:", err);
            chatContactsList.innerHTML = `<p class="system-msg">❌ خطا در ارتباط با سرور: ${err.message}</p>`;
        }
    }
});