// frontend/js/login.js

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  const phoneRegex = /^09\d{9}$/;
  if (!phoneRegex.test(username)) {
    alert("شماره تلفن معتبر نیست. مثال: 09123456789");
    return;
  }

  if (password.length < 8) {
    alert("رمز عبور باید حداقل ۸ کاراکتر باشد.");
    return;
  }

  try {
    const response = await fetch("http://localhost:8000/v1/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: username,
        password: password,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      alert("❌ " + (result.detail || "ورود ناموفق بود."));
      return;
    }

    const token = result.access_token;
    const tokenType = result.token_type;

    if (!token) {
      alert("❌ توکن دریافتی نامعتبر است.");
      return;
    }

    function base64UrlDecode(str) {
      str = str.replace(/-/g, "+").replace(/_/g, "/");
      while (str.length % 4) {
        str += "=";
      }
      return atob(str);
    }

    const payloadBase64 = token.split(".")[1];
    const decodedPayload = JSON.parse(base64UrlDecode(payloadBase64));
    console.log("Decoded JWT payload:", decodedPayload);

    const user = {
      id: parseInt(decodedPayload.sub, 10),
      username: decodedPayload.username,
      is_admin: decodedPayload.is_admin,
      is_employer: decodedPayload.is_employer,
    };
    localStorage.setItem("access_token", token);
    localStorage.setItem("token_type", tokenType);
    localStorage.setItem("user", JSON.stringify(user)); // Store user object

    alert("✅ ورود موفقیت‌آمیز بود!");

    // ✅ منطق جدید: بررسی وجود redirect_job_id
    const redirectJobId = localStorage.getItem("redirect_job_id");
    if (redirectJobId) {
      localStorage.removeItem("redirect_job_id"); // پاک کردن پس از استفاده
      window.location.href = `job.html?id=${redirectJobId}`; // هدایت به صفحه جزئیات شغل
    } else if (user.is_admin === true || user.is_admin === "true") {
      window.location.href = "admin.html";
    } else if (user.is_employer === true || user.is_employer === "true") {
      window.location.href = "employer_dashboard.html"; // Redirect to employer dashboard
    } else {
      window.location.href = "home.html"; // Redirect to job seeker home
    }

  } catch (error) {
    console.error("Login error:", error);
    alert("⚠️ خطا در ورود: " + error.message);
  }
});

// Google Login Button Handler
document.getElementById("googleLoginBtn").addEventListener("click", async () => {
  try {
    const response = await fetch("http://localhost:8000/v1/auth/google");
    const data = await response.json();
    if (response.ok && data.url) {
      // ✅ اگر کاربر از طریق لینک جزئیات شغل به اینجا رسیده، job_id را برای ریدایرکت پس از گوگل لاگین هم ذخیره کنیم
      const currentUrlParams = new URLSearchParams(window.location.search);
      const jobIdFromUrl = currentUrlParams.get('job_id'); // اگر job_id در URL هنگام کلیک روی گوگل لاگین بود
      if (jobIdFromUrl) {
          localStorage.setItem("redirect_job_id", jobIdFromUrl);
      }
      window.location.href = data.url; // Redirect to Google OAuth Consent Screen
    } else {
      alert("❌ خطا در شروع ورود با گوگل.");
    }
  } catch (error) {
    console.error("Google login initiation error:", error);
    alert("⚠️ خطا در ارتباط با سرویس گوگل: " + error.message);
  }
});