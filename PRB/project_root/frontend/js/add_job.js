document.addEventListener("DOMContentLoaded", async () => {
    const addJobForm = document.getElementById("addJobForm");
    const citySelect = document.getElementById("city_id");
    const token = localStorage.getItem("access_token");
    const user = JSON.parse(localStorage.getItem("user"));

    if (!token || !user || !user.is_employer) {
        alert("❌ فقط کارفرمایان مجاز به ثبت شغل هستند. لطفاً وارد حساب کارفرمایی خود شوید.");
        window.location.href = "login.html";
        return;
    }

    // بارگذاری شهرها
    try {
        const citiesResponse = await fetch("http://localhost:8000/v1/cities");
        if (!citiesResponse.ok) throw new Error("خطا در بارگذاری شهرها.");
        const cities = await citiesResponse.json();
        cities.forEach(city => {
            const option = document.createElement("option");
            option.value = city.id;
            option.textContent = city.name;
            citySelect.appendChild(option);
        });
    } catch (error) {
        alert("❌ خطا در بارگذاری لیست شهرها: " + error.message);
        console.error("Error loading cities:", error);
    }

    addJobForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const title = document.getElementById("title").value.trim();
        const description = document.getElementById("description").value.trim();
        const city_id = parseInt(document.getElementById("city_id").value);
        const employer_info = document.getElementById("employer_info").value.trim();

        if (!title || !description || isNaN(city_id) || city_id === 0) { // city_id === 0 برای حالتی که "شهر را انتخاب کنید" انتخاب شده
            alert("لطفاً همه‌ی فیلدهای الزامی را کامل کنید.");
            return;
        }

        const jobData = {
            title,
            description,
            city_id,
            employer_id: user.id, // استفاده از user.id کارفرمای فعلی
            employer_info: employer_info || null,
        };

        try {
            const response = await fetch("http://localhost:8000/v1/employer/jobs", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify(jobData),
            });

            const result = await response.json();

            if (!response.ok) {
                let message = "ثبت شغل ناموفق بود.";
                if (result.detail) {
                    message = typeof result.detail === "string" ? result.detail : result.detail[0]?.msg || message;
                }
                alert("❌ " + message);
                return;
            }

            alert("✅ شغل با موفقیت ثبت شد و پس از تأیید مدیر نمایش داده خواهد شد!");
            addJobForm.reset(); // پاک کردن فرم
            window.location.href = "employer_dashboard.html"; // برگشت به داشبورد
        } catch (error) {
            alert("⚠️ خطا در ثبت شغل: " + error.message);
            console.error("Add job error:", error);
        }
    });
});