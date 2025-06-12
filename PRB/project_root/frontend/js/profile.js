// frontend/js/profile.js

document.addEventListener("DOMContentLoaded", async () => {
    const userProfileInfo = document.getElementById("user-profile-info");
    const token = localStorage.getItem("access_token");
    const user = JSON.parse(localStorage.getItem("user"));

    if (!token || !user) {
        userProfileInfo.innerHTML = "<p class='system-msg'>❌ برای مشاهده پروفایل، لطفاً وارد شوید.</p>";
        setTimeout(() => {
            window.location.href = "login.html";
        }, 2000);
        return;
    }

    try {
        const response = await fetch("http://localhost:8000/v1/user/me", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "خطا در دریافت اطلاعات پروفایل.");
        }

        const userData = await response.json();

        userProfileInfo.innerHTML = `
            <p><strong>نام کاربری (شماره تلفن):</strong> ${userData.username}</p>
            <p><strong>نام:</strong> ${userData.first_name}</p>
            <p><strong>نام خانوادگی:</strong> ${userData.last_name}</p>
            <p><strong>استان:</strong> ${userData.province}</p>
            <p><strong>نقش:</strong> ${userData.is_admin ? 'مدیر' : (userData.is_employer ? 'کارفرما' : 'کارجو')}</p>
        `;
    } catch (error) {
        console.error("Error fetching user profile:", error);
        userProfileInfo.innerHTML = `<p class='system-msg'>❌ خطا در بارگذاری اطلاعات پروفایل: ${error.message}</p>`;
    }
});